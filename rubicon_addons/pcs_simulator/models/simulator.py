import math
import random
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

# Routing from the company audit (meta/audit.pdf, "Production Process"):
# the metal frame and the stones advance in parallel and join at Merged.
PROD_ROUTE = ['WAX', 'CST', 'QC1', 'FIL', 'QC2', 'PPL', 'QC3', 'ASM', 'QC4',
              'MER', 'SET', 'QC5', 'POL', 'QC6', 'ENG', 'QC7', 'PLT', 'QC8',
              'FIN']
STONE_ROUTE = ['AST', 'SHP', 'CUT', 'SRD', 'SFN']

# A failed quality check sends the piece to a repair department, then back
# to the same check ("Repairing if needed" in the audit).
QC_REPAIR = {'QC1': 'QC11', 'QC2': 'QC11', 'QC3': 'QC11', 'QC4': 'QC11',
             'QC5': 'RST', 'QC6': 'QC11', 'QC7': 'QC11', 'QC8': 'QC11'}
QC_FAIL_PROBABILITY = 0.08

# Mean processing time per department, in hours.
MEAN_HOURS = {
    'WAX': 16, 'CST': 8, 'QC1': 2, 'FIL': 12, 'QC2': 2, 'PPL': 8, 'QC3': 2,
    'ASM': 12, 'QC4': 2, 'MER': 4, 'SET': 10, 'QC5': 2, 'POL': 6, 'QC6': 2,
    'ENG': 4, 'QC7': 2, 'PLT': 6, 'QC8': 3, 'FIN': 4,
    'AST': 6, 'SHP': 10, 'CUT': 12, 'SRD': 2, 'SFN': 1,
    'QC11': 6, 'RST': 8,
}

DEFAULT_GOLD_WEIGHT = 5.0


class PcsSimulator(models.Model):
    """Factory simulator: advances pieces through the production process
    by calling the real scan API, so dashboards, reports and the operations
    timeline fill up exactly as they would with physical scanners.
    """
    _name = 'pcs.simulator'
    _description = 'PCS Factory Simulator'

    name = fields.Char(default='Factory Simulator')
    sim_time = fields.Datetime(string='Simulated Clock')
    tick_count = fields.Integer(default=0)
    seed = fields.Integer(default=42)
    document_ids = fields.Many2many('pcs.document', string='Simulated Documents')
    employee_ids = fields.Many2many('pcs.employee', string='Simulated Workers')

    @api.model
    def _get(self):
        simulator = self.search([], limit=1)
        return simulator or self.create({})

    # ── Setup / reset ──────────────────────────────────────────────────────

    @api.model
    def setup(self, n_orders=3, days_back=30, references=None):
        """Create simulated workers and register sales orders in production.

        `references` forces specific SO names (used by tests); otherwise the
        most recent sales orders not yet in PCS are picked.
        """
        simulator = self._get()
        simulator._ensure_employees()

        SisDoc = self.env['sis.document']
        if references:
            sis_docs = SisDoc.search([('name', 'in', references)])
        else:
            candidates = SisDoc.search(
                [('doc_type_code', '=', 'SO')], order='name desc', limit=200)
            in_pcs = self.env['pcs.document'].with_context(
                active_test=False).search([]).mapped('sis_document_id')
            sis_docs = candidates.filtered(
                lambda d: d not in in_pcs
                and any(i.product_id for i in d.item_ids))[:n_orders]
        if not sis_docs:
            raise UserError("No suitable sales order found to simulate.")

        Document = self.env['pcs.document']
        for sis_doc in sis_docs:
            existing = Document.with_context(active_test=False).search(
                [('sis_document_id', '=', sis_doc.id)], limit=1)
            doc = existing or Document.browse(
                Document.create_from_reference(sis_doc.name))
            doc.simulated = True
            simulator.document_ids |= doc

        if not simulator.sim_time:
            simulator.sim_time = (fields.Datetime.now()
                                  - timedelta(days=days_back))
        return simulator.get_status()

    def _ensure_employees(self):
        self.ensure_one()
        Employee = self.env['pcs.employee']
        employees = Employee.browse()
        for code in MEAN_HOURS:
            dept = self.env.ref('pcs_document.dept_%s' % code.lower(),
                                raise_if_not_found=False)
            if not dept:
                continue
            for i in (1, 2):
                emp_code = 'S%s%d' % (code, i)
                employee = Employee.with_context(active_test=False).search(
                    [('code', '=', emp_code)], limit=1)
                if not employee:
                    employee = Employee.create({
                        'code': emp_code,
                        'name': 'Sim %s %d' % (dept.name, i),
                        'tag': 'SIM',
                        'department_ids': [(6, 0, [dept.id])],
                    })
                employees |= employee
        self.employee_ids = [(6, 0, employees.ids)]

    @api.model
    def reset(self):
        """Remove all simulated production data (documents stay in SIS)."""
        simulator = self._get()
        docs = simulator.document_ids
        self.env['pcs.transaction'].search(
            [('document_id', 'in', docs.ids)]).unlink()
        simulator.document_ids = [(5, 0, 0)]
        docs.unlink()
        simulator.write({'sim_time': False, 'tick_count': 0})
        return True

    # ── Engine ─────────────────────────────────────────────────────────────

    @api.model
    def tick(self, hours=8):
        """Advance the simulated clock and let every piece progress."""
        simulator = self._get()
        if not simulator.document_ids:
            raise UserError("Run the setup first.")
        if not simulator.sim_time:
            simulator.sim_time = fields.Datetime.now()
        simulator.sim_time += timedelta(hours=hours)
        simulator.tick_count += 1
        rng = random.Random(simulator.seed * 100000 + simulator.tick_count)

        for barcode in simulator.document_ids.mapped('barcode_ids'):
            if simulator._is_finished(barcode):
                continue
            if barcode.product_id and barcode.product_id.stone_line_ids:
                simulator._advance_track(barcode, 'stone', STONE_ROUTE,
                                         rng, hours)
            simulator._advance_track(barcode, 'prod', PROD_ROUTE, rng, hours)
        return simulator.get_status()

    @api.model
    def run_history(self, days=30, tick_hours=8):
        """Fast-forward: generate `days` of factory history in one call."""
        simulator = self._get()
        status = None
        for _ in range(int(days * 24 / tick_hours)):
            status = self.tick(tick_hours)
        return status

    @api.model
    def advance_hours(self, hours, chunk=8):
        """Advance an arbitrary number of hours. Large jumps are split into
        chunks so pieces can traverse several departments on the way (a
        single tick only ever moves a piece by one step)."""
        remaining = float(hours)
        status = None
        while remaining > 0:
            step = min(chunk, remaining)
            status = self.tick(step)
            remaining -= step
        return status

    @api.model
    def step_operation(self, max_hours=720, step_hours=1):
        """Advance hour by hour until at least one operation happens
        (a piece issued to a department or received back), then stop."""
        simulator = self._get()
        Transaction = self.env['pcs.transaction']

        def counts():
            issues = Transaction.search_count(
                [('document_id', 'in', simulator.document_ids.ids)])
            receives = Transaction.search_count([
                ('document_id', 'in', simulator.document_ids.ids),
                ('status', '=', 'fin')])
            return issues, receives

        before = counts()
        hours = 0
        status = None
        while hours < max_hours:
            status = self.tick(step_hours)
            hours += step_hours
            if counts() != before:
                status['event'] = True
                status['elapsed_hours'] = hours
                status['event_lines'] = self._current_tick_events(simulator)
                return status
        status = status or self.get_status()
        status['event'] = False
        return status

    def _current_tick_events(self, simulator):
        """Human-readable list of what just happened (current sim time)."""
        lines = []
        txns = self.env['pcs.transaction'].search(
            [('document_id', 'in', simulator.document_ids.ids)])
        for txn in txns:
            if txn.issue_date == simulator.sim_time:
                lines.append('%s sent to %s' % (
                    txn.barcode_id.name, txn.department_id.name))
            if txn.receive_date == simulator.sim_time:
                lines.append('%s finished in %s' % (
                    txn.barcode_id.name, txn.department_id.name))
        return lines

    def _is_finished(self, barcode):
        last = barcode._last_transaction('prod')
        return bool(last and last.status == 'fin'
                    and last.department_id.code == PROD_ROUTE[-1])

    def _advance_track(self, barcode, track, route, rng, hours):
        self.ensure_one()
        last = barcode._last_transaction(track)
        if not last:
            self._sim_issue(barcode, route[0], rng)
            return
        code = last.department_id.code
        if last.status == 'wip':
            mean = MEAN_HOURS.get(code, 8)
            if rng.random() < 1 - math.exp(-hours / mean):
                self._sim_receive(barcode, last, rng)
                if (code in QC_REPAIR
                        and rng.random() < QC_FAIL_PROBABILITY):
                    self._sim_issue(barcode, QC_REPAIR[code], rng)
            return
        # Last operation finished: route to the next department.
        if code in QC_REPAIR.values():
            failed_qc = self._qc_before_repair(barcode, track)
            if failed_qc:
                self._sim_issue(barcode, failed_qc, rng)
            return
        if code not in route:
            return
        index = route.index(code)
        if index + 1 >= len(route):
            return
        next_code = route[index + 1]
        if next_code == 'MER' and not self._stones_ready(barcode):
            return
        self._sim_issue(barcode, next_code, rng)

    def _qc_before_repair(self, barcode, track):
        """The QC that sent the piece to repair: the transaction right
        before the repair one on the same track."""
        txns = barcode.transaction_ids.sorted(lambda t: t.id).filtered(
            lambda t: t.department_id.track == track)
        if (len(txns) >= 2
                and txns[-1].department_id.code in QC_REPAIR.values()):
            return txns[-2].department_id.code
        return None

    def _stones_ready(self, barcode):
        if not (barcode.product_id and barcode.product_id.stone_line_ids):
            return True
        last = barcode._last_transaction('stone')
        return bool(last and last.status == 'fin'
                    and last.department_id.code == STONE_ROUTE[-1])

    # ── Scan helpers (real API + simulated clock) ──────────────────────────

    def _dept(self, code):
        return self.env.ref('pcs_document.dept_%s' % code.lower())

    def _worker_for(self, dept, rng):
        workers = self.employee_ids.filtered(lambda e: dept in e.department_ids)
        return rng.choice(workers) if workers else self.env['pcs.employee']

    def _current_weight(self, barcode):
        for txn in barcode.transaction_ids.sorted(lambda t: t.id, reverse=True):
            if txn.department_id.track != 'prod':
                continue
            if txn.receive_weight:
                return txn.receive_weight
            if txn.issue_weight:
                return txn.issue_weight
        return barcode._gold_weight() or DEFAULT_GOLD_WEIGHT

    def _current_stone_weight(self, barcode):
        for txn in barcode.transaction_ids.sorted(lambda t: t.id, reverse=True):
            if txn.receive_stone_weight:
                return txn.receive_stone_weight
            if txn.issue_stone_weight:
                return txn.issue_stone_weight
        product = barcode.product_id
        return (product.total_stone_weight if product else 0.0) or 1.0

    def _scan_weights(self, barcode, dept):
        """(gold g, stone ct) to pass on a scan, per the department needs
        — so the simulation also satisfies the 'required' weight-control
        mode when it is enabled."""
        needs = self.env['pcs.transaction']._weight_needs(dept)
        gold = round(self._current_weight(barcode), 3) if 'gold' in needs else 0.0
        stone = (round(self._current_stone_weight(barcode), 3)
                 if 'stone' in needs else 0.0)
        return gold, stone

    def _sim_issue(self, barcode, dept_code, rng):
        dept = self._dept(dept_code)
        worker = self._worker_for(dept, rng)
        gold, stone = self._scan_weights(barcode, dept)
        result = self.env['pcs.transaction'].scan(
            barcode.name, dept.id, worker.id or False, gold, stone)
        if result.get('status') == 'issued':
            self.env['pcs.transaction'].browse(
                result['transaction_id']).issue_date = self.sim_time

    def _sim_receive(self, barcode, txn, rng):
        dept = txn.department_id
        gold, stone = self._scan_weights(barcode, dept)
        if gold and dept.loss_pct:
            factor = dept.loss_pct / 100.0
            gold = round(gold * (1 - factor * rng.uniform(0.5, 1.5)), 3)
        if stone and dept.code in ('SHP', 'CUT'):
            # Shaping and cutting remove material from the stones.
            stone = round(stone * (1 - rng.uniform(0.05, 0.15)), 3)
        result = self.env['pcs.transaction'].scan(
            barcode.name, dept.id, txn.employee_id.id or False, gold, stone)
        if result.get('status') == 'received':
            txn.receive_date = self.sim_time

    # ── Status for the UI ──────────────────────────────────────────────────

    @api.model
    def get_status(self):
        simulator = self._get()
        documents = []
        for doc in simulator.document_ids:
            barcodes = doc.barcode_ids
            done = len([b for b in barcodes if simulator._is_finished(b)])
            positions = []
            for barcode in barcodes:
                last = barcode._last_transaction('prod')
                if last:
                    positions.append('%s %s' % (
                        last.department_id.code,
                        'WIP' if last.status == 'wip' else 'FIN'))
            documents.append({
                'id': doc.id,
                'name': doc.name,
                'pieces': len(barcodes),
                'done': done,
                'positions': ', '.join(positions),
            })

        txns = self.env['pcs.transaction'].search(
            [('document_id', 'in', simulator.document_ids.ids)],
            order='id desc', limit=40)
        events = [{
            'id': t.id,
            'time': (t.receive_date or t.issue_date).strftime('%d/%m/%Y %H:%M')
                    if (t.receive_date or t.issue_date) else '',
            'barcode': t.barcode_id.name,
            'dept': t.department_id.name,
            'status': 'WIP' if t.status == 'wip' else 'FIN',
            'worker': t.employee_id.name or '',
            'issue_weight': t.issue_weight,
            'receive_weight': t.receive_weight,
        } for t in txns]

        return {
            'sim_time': simulator.sim_time.strftime('%d/%m/%Y %H:%M')
                        if simulator.sim_time else '',
            'tick_count': simulator.tick_count,
            'seed': simulator.seed,
            'attached': self.is_attached(),
            'documents': documents,
            'events': events,
        }

    # ── Attached / detached from the PCS screens ───────────────────────────

    @api.model
    def is_attached(self):
        """Same switch as the PCS workspace 'Include simulation data'."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'pcs.include_simulated', '1') == '1'

    @api.model
    def set_attached(self, attached):
        self.env['ir.config_parameter'].sudo().set_param(
            'pcs.include_simulated', '1' if attached else '0')
        return True

    @api.model
    def scan_piece(self, barcode_value, department_id, employee_id=False,
                   weight=None, stone_weight=None, note=None):
        """Virtual scanner: same real scan API a physical station uses,
        with the transaction stamped at the simulated clock."""
        simulator = self._get()
        result = self.env['pcs.transaction'].scan(
            barcode_value, department_id, employee_id, weight,
            stone_weight, note)
        if simulator.sim_time and result.get('transaction_id'):
            txn = self.env['pcs.transaction'].browse(result['transaction_id'])
            if result.get('status') == 'issued':
                txn.issue_date = simulator.sim_time
            elif result.get('status') == 'received':
                txn.receive_date = simulator.sim_time
        return result

    @api.model
    def get_pieces(self):
        """The simulated pieces with their barcode, exactly as printed on
        the stock cards, so the UI can offer a virtual scanner."""
        simulator = self._get()
        pieces = []
        for barcode in simulator.document_ids.mapped('barcode_ids').sorted(
                lambda b: (b.document_id.name or '', b.line_no)):
            prod_dept, prod_status = barcode.track_status('prod')
            stone_dept, stone_status = barcode.track_status('stone')
            pieces.append({
                'id': barcode.id,
                'barcode': barcode.name,
                'barcode_url': barcode.barcode_image_url(),
                'design': barcode.design or '',
                'document': barcode.document_id.name,
                'prod_position': ('%s %s' % (prod_dept.name, prod_status)
                                  if prod_dept else 'Not started'),
                'stone_position': ('%s %s' % (stone_dept.name, stone_status)
                                   if stone_dept else ''),
                'done': simulator._is_finished(barcode),
            })
        return pieces

    @api.model
    def get_flow(self):
        """Data for the schematic factory map: piece counts per department
        and the transfers that happened during the current tick."""
        simulator = self._get()
        barcodes = simulator.document_ids.mapped('barcode_ids')
        txns = self.env['pcs.transaction'].search(
            [('barcode_id', 'in', barcodes.ids)], order='id')

        nodes = {
            dept.code: {'name': dept.name, 'is_qc': dept.is_qc,
                        'wip': 0, 'fin': 0}
            for dept in self.env['pcs.department'].search([])
        }
        latest = {}
        for txn in txns:
            latest[(txn.barcode_id.id, txn.department_id.track)] = txn
        for txn in latest.values():
            qty = int(txn.barcode_id.qty) or 1
            bucket = 'wip' if txn.status == 'wip' else 'fin'
            nodes[txn.department_id.code][bucket] += qty

        # Transfers of the current tick: transactions issued at the current
        # simulated time, traced back to the previous department of the
        # same piece on the same track ('' = entering the factory).
        transfers = {}
        previous = {}
        for txn in txns:
            key = (txn.barcode_id.id, txn.department_id.track)
            if simulator.sim_time and txn.issue_date == simulator.sim_time:
                origin = previous.get(key)
                pair = (origin.department_id.code if origin else '',
                        txn.department_id.code)
                transfers[pair] = transfers.get(pair, 0) + (
                    int(txn.barcode_id.qty) or 1)
            previous[key] = txn

        return {
            'sim_time': simulator.sim_time.strftime('%d/%m/%Y %H:%M')
                        if simulator.sim_time else '',
            'total_pieces': len(barcodes),
            'done': len([b for b in barcodes if simulator._is_finished(b)]),
            'nodes': nodes,
            'transfers': [
                {'origin': origin, 'to': to, 'count': count}
                for (origin, to), count in transfers.items()
            ],
        }

    @api.model
    def set_seed(self, seed):
        self._get().seed = int(seed)
        return True
