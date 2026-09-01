from odoo import models, fields, api

# The two QC scales: metal is weighed in grams, stones in carats.
GRAMS_TO_CARATS = 5.0

WEIGHT_CONTROL_PARAM = 'pcs.weight_control'
WEIGHT_CONTROL_MODES = ('off', 'optional', 'required')


class PcsTransaction(models.Model):
    """One pass of a piece through a department (issue -> receive).

    Scanning the piece's stock card in a department toggles the transaction:
    the first scan issues the piece to the department (WIP), the second scan
    receives it back (FIN). The production and stone tracks are independent,
    so a piece may hold one open transaction on each track at the same time.
    """
    _name = 'pcs.transaction'
    _description = 'PCS Department Transaction'
    _rec_name = 'pbarcode'
    _order = 'id desc'

    barcode_id = fields.Many2one(
        'pcs.barcode', string='Barcode', required=True,
        ondelete='cascade', index=True)
    document_id = fields.Many2one(
        related='barcode_id.document_id', store=True, index=True)
    department_id = fields.Many2one(
        'pcs.department', string='Dept', required=True, index=True)
    employee_id = fields.Many2one('pcs.employee', string='Worker')
    status = fields.Selection(
        [('wip', 'WIP'), ('fin', 'FIN')], required=True, default='wip',
        index=True)
    issue_date = fields.Datetime(
        string='Issue Date', default=fields.Datetime.now)
    receive_date = fields.Datetime(string='Receive Date')
    issue_weight = fields.Float(string='Issue Wht. (g)', digits=(10, 3))
    receive_weight = fields.Float(string='Rcvd. Wht. (g)', digits=(10, 3))
    issue_stone_weight = fields.Float(
        string='Issue Stone Wht. (ct)', digits=(10, 3))
    receive_stone_weight = fields.Float(
        string='Rcvd. Stone Wht. (ct)', digits=(10, 3))
    note = fields.Char(
        string='Note',
        help="Weighing anomalies: stone swapped, missing, or one too many "
             "(PDP error).")
    pbarcode = fields.Char(
        string='PBarcode', compute='_compute_pbarcode', store=True)

    @api.depends('barcode_id.name', 'department_id.sequence',
                 'department_id.group_id.type')
    def _compute_pbarcode(self):
        for txn in self:
            if not (txn.barcode_id and txn.department_id):
                txn.pbarcode = False
                continue
            txn.pbarcode = '%s-%s' % (
                txn.department_id.pbarcode_prefix(), txn.barcode_id.name)

    # ── Weight control (optional operating mode) ───────────────────────────

    @api.model
    def weight_control_mode(self):
        """'off' (legacy behaviour), 'optional' (weighing fields offered)
        or 'required' (the scan blocks until the weights are entered)."""
        mode = self.env['ir.config_parameter'].sudo().get_param(
            WEIGHT_CONTROL_PARAM, 'off')
        return mode if mode in WEIGHT_CONTROL_MODES else 'off'

    @api.model
    def set_weight_control_mode(self, mode):
        if mode not in WEIGHT_CONTROL_MODES:
            raise ValueError("Invalid weight control mode: %r" % mode)
        self.env['ir.config_parameter'].sudo().set_param(
            WEIGHT_CONTROL_PARAM, mode)
        return True

    @api.model
    def _weight_needs(self, department):
        """Which weights a department captures, from its legacy flags:
        gold in grams on the metal scale, stones in carats on the other."""
        needs = []
        if department.track == 'prod' and (
                department.metals or department.auto_weight
                or department.loss_pct):
            needs.append('gold')
        if department.stones or (
                department.track == 'stone' and department.auto_weight):
            needs.append('stone')
        return needs

    # ── Scan endpoint ──────────────────────────────────────────────────────

    @api.model
    def scan(self, barcode_value, department_id, employee_id=False,
             weight=None, stone_weight=None, note=None):
        """Register a scan of a stock card in a department.

        Toggle semantics per track: no open transaction -> issue (WIP);
        open transaction in the scanned department -> receive (FIN); open
        transaction in another department of the same track -> refused.
        `weight` is gold in grams, `stone_weight` stones in carats; under
        the 'required' weight-control mode the scan returns a
        'weight_required' status until the department's weights are given.
        Returns a dict the scan station can display directly.
        """
        Barcode = self.env['pcs.barcode']
        name = Barcode.clean_scanned_value(barcode_value)
        barcode = Barcode.search([('name', '=', name)], limit=1)
        if not barcode:
            return {'status': 'error',
                    'message': "Unknown barcode '%s'." % name}
        if not barcode.document_id.active:
            return {'status': 'error',
                    'message': "Document %s is deactivated."
                               % barcode.document_id.name}
        department = self.env['pcs.department'].browse(int(department_id))
        if not department.exists():
            return {'status': 'error', 'message': "Unknown department."}

        open_txns = self.search([
            ('barcode_id', '=', barcode.id), ('status', '=', 'wip')])
        same_track = open_txns.filtered(
            lambda t: t.department_id.track == department.track)

        product = barcode.product_id
        info = {
            'barcode': barcode.name,
            'design': barcode.design or '',
            'purity': barcode.purity or '',
            'qty': barcode.qty,
            'department': department.name,
            'expected_stone_weight': round(product.total_stone_weight, 2)
                                     if product else 0.0,
        }

        if same_track and same_track[0].department_id == department:
            action = 'receive'
        elif same_track:
            blocking = same_track[0]
            return dict(info, status='error',
                        message="%s is still WIP in %s; receive it there first."
                                % (barcode.name, blocking.department_id.name))
        else:
            action = 'issue'

        if self.weight_control_mode() == 'required':
            needs = self._weight_needs(department)
            provided = {'gold': weight, 'stone': stone_weight}
            missing = [n for n in needs if not provided[n]]
            if missing:
                return dict(info, status='weight_required', action=action,
                            needs=needs, missing=missing,
                            message="Weighing required in %s: %s."
                                    % (department.name, ', '.join(missing)))

        if action == 'receive':
            txn = same_track[0]
            values = {
                'status': 'fin',
                'receive_date': fields.Datetime.now(),
                'receive_weight': weight or 0.0,
                'receive_stone_weight': stone_weight or 0.0,
                'employee_id': int(employee_id) if employee_id else txn.employee_id.id,
            }
            if note:
                values['note'] = ('%s | %s' % (txn.note, note)
                                  if txn.note else note)
            txn.write(values)
            return dict(info, status='received', transaction_id=txn.id,
                        message="%s received in %s." % (barcode.name, department.name))

        txn = self.create({
            'barcode_id': barcode.id,
            'department_id': department.id,
            'employee_id': int(employee_id) if employee_id else False,
            'issue_weight': weight or 0.0,
            'issue_stone_weight': stone_weight or 0.0,
            'note': note or False,
        })
        return dict(info, status='issued', transaction_id=txn.id,
                    message="%s issued to %s." % (barcode.name, department.name))
