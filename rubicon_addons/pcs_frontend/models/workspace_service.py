import re

from odoo import api, fields, models

# Doc Items Dept Cost / Dashboard Summary columns -> department codes
DEPT_COST_COLUMNS = [
    ('casting', 'CST'), ('cutting', 'CUT'), ('filling', 'FIL'),
    ('setting', 'SET'), ('assembly', 'ASM'), ('polishing', 'POL'),
    ('plating', 'PLT'),
]
SUMMARY_COLUMNS = [
    ('casting', 'CST'), ('filling', 'FIL'), ('qc_pre_polish', 'QC3'),
    ('qc_assembly', 'QC4'), ('assort', 'AST'), ('shape', 'SHP'),
    ('cut', 'CUT'), ('stone_ready', 'SRD'), ('stone', 'STN'),
    ('merged', 'MER'), ('qc_set', 'QC5'), ('qc_polish', 'QC6'),
    ('qc_final', 'QC8'),
]


def _d(value):
    """dd/mm/yyyy or '' (legacy PCS date format)."""
    return value.strftime('%d/%m/%Y') if value else ''


def _dt(value):
    return value.strftime('%d/%m/%Y %H:%M') if value else ''


def _purity_fraction(purity):
    """'18K' -> 0.75, '925' -> 0.925, unknown -> 1.0."""
    purity = (purity or '').strip().upper()
    match = re.match(r'^(\d+(?:\.\d+)?)K$', purity)
    if match:
        return float(match.group(1)) / 24.0
    match = re.match(r'^(\d{3})$', purity)
    if match:
        return int(match.group(1)) / 1000.0
    return 1.0


class PcsWorkspaceService(models.TransientModel):
    """RPC backend of the PCS OWL workspace: one method per screen."""
    _name = 'pcs.workspace.service'
    _description = 'PCS workspace helper methods'

    # ── Shared helpers ─────────────────────────────────────────────────────

    def _latest_track_txns(self, barcodes):
        """{(barcode_id, track): last transaction} for the given barcodes."""
        txns = self.env['pcs.transaction'].search(
            [('barcode_id', 'in', barcodes.ids)], order='id')
        latest = {}
        for txn in txns:
            latest[(txn.barcode_id.id, txn.department_id.track)] = txn
        return latest

    def _sim_included(self):
        """Whether simulated documents are hooked into the PCS screens."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'pcs.include_simulated', '1') == '1'

    def _doc_domain(self, domain=None):
        domain = list(domain or [])
        if not self._sim_included():
            domain.append(('simulated', '=', False))
        return domain

    def _active_barcodes(self):
        domain = [('document_id.active', '=', True)]
        if not self._sim_included():
            domain.append(('document_id.simulated', '=', False))
        return self.env['pcs.barcode'].search(domain)

    @api.model
    def get_sim_mode(self):
        return {
            'include': self._sim_included(),
            'has_sim': bool(self.env['pcs.document'].with_context(
                active_test=False).search_count(
                    [('simulated', '=', True)], limit=1)),
        }

    @api.model
    def set_sim_mode(self, include):
        self.env['ir.config_parameter'].sudo().set_param(
            'pcs.include_simulated', '1' if include else '0')
        return True

    # ── Activities / Sales Documents ───────────────────────────────────────

    @api.model
    def get_sales_docs(self):
        docs = self.env['sis.document'].search(
            [('doc_type_code', '=', 'SO')],
            order='date_created desc, name desc')
        return [{
            'id': d.id,
            'name': d.name,
            'create_date': _d(d.date_created),
            'delv_date': _d(d.date_due),
            'total_qty': d.total_qty,
        } for d in docs]

    @api.model
    def get_sales_doc_items(self, doc_id):
        doc = self.env['sis.document'].browse(int(doc_id))
        return [{
            'id': item.id,
            'design': item.design or '',
            'purity': item.purity or '',
            'qty': item.qty,
            'unk_id': item.id,
        } for item in doc.item_ids.sorted(lambda i: (i.sequence, i.id))]

    # ── Activities / Documents ─────────────────────────────────────────────

    @api.model
    def get_documents(self, active_only=True):
        domain = [('active', '=', True)] if active_only else []
        docs = self.env['pcs.document'].with_context(
            active_test=False).search(self._doc_domain(domain),
                                      order='name desc')
        return [{
            'id': d.id,
            'name': d.name,
            'date': _d(d.date),
            'active': d.active,
            'create_date': _dt(d.create_date),
            'created_by': d.create_uid.name or '',
        } for d in docs]

    @api.model
    def add_document(self, reference):
        doc_id = self.env['pcs.document'].create_from_reference(reference)
        return doc_id

    @api.model
    def set_document_active(self, doc_id, active):
        doc = self.env['pcs.document'].with_context(
            active_test=False).browse(int(doc_id))
        doc.active = bool(active)
        return True

    @api.model
    def delete_document(self, doc_id):
        doc = self.env['pcs.document'].with_context(
            active_test=False).browse(int(doc_id))
        doc.unlink()
        return True

    @api.model
    def update_pdp(self, doc_id):
        doc = self.env['pcs.document'].browse(int(doc_id))
        doc.action_update_pdp()
        return True

    @api.model
    def get_barcodes(self, doc_id):
        doc = self.env['pcs.document'].browse(int(doc_id))
        return [{
            'id': b.id,
            'barcode': b.name,
            'design': b.design or '',
            'purity': b.purity or '',
            'qty': b.qty,
            'tag': b.tag or '',
            'priority': b.priority,
        } for b in doc.barcode_ids.sorted('line_no')]

    @api.model
    def update_barcode(self, barcode_id, values):
        allowed = {k: v for k, v in values.items() if k in ('tag', 'priority')}
        if allowed:
            self.env['pcs.barcode'].browse(int(barcode_id)).write(allowed)
        return True

    @api.model
    def get_pbarcodes(self, doc_id):
        txns = self.env['pcs.transaction'].search(
            [('document_id', '=', int(doc_id))], order='id')
        return [{
            'id': t.id,
            'pbarcode': t.pbarcode or '',
            'dept': t.department_id.name or '',
            'worker': t.employee_id.name or '',
            'trans_id': t.id,
            'updated_by': t.write_uid.name or '',
        } for t in txns]

    # ── Activities / Dashboard ─────────────────────────────────────────────

    @api.model
    def get_dashboard(self, panel='prod', barcode=None, document_id=None,
                      party_id=None):
        barcodes = self._active_barcodes()
        if barcode:
            cleaned = self.env['pcs.barcode'].clean_scanned_value(barcode)
            barcodes = barcodes.filtered(
                lambda b: cleaned.lower() in (b.name or '').lower())
        if document_id:
            barcodes = barcodes.filtered(
                lambda b: b.document_id.id == int(document_id))
        if party_id:
            barcodes = barcodes.filtered(
                lambda b: b.document_id.sis_document_id.party_id.id
                == int(party_id))

        latest = self._latest_track_txns(barcodes)
        work, finish = {}, {}
        for txn in latest.values():
            qty = int(txn.barcode_id.qty) or 1
            counter = work if txn.status == 'wip' else finish
            counter[txn.department_id.id] = counter.get(
                txn.department_id.id, 0) + qty

        depts = self.env['pcs.department'].search([]).filtered(
            lambda dpt: dpt.track == panel and dpt.code != 'OFF')
        cells = [{
            'id': dpt.id,
            'code': dpt.code,
            'name': dpt.name,
            'work': work.get(dpt.id, 0),
            'finish': finish.get(dpt.id, 0),
        } for dpt in depts.sorted(lambda dpt: (dpt.sequence, dpt.code))]
        return {
            'cells': cells,
            'total_pieces': int(sum(barcodes.mapped('qty'))),
        }

    @api.model
    def get_order_filters(self):
        docs = self.env['pcs.document'].search(self._doc_domain())
        parties = docs.mapped('sis_document_id.party_id')
        return {
            'companies': [{'id': p.id, 'name': p.name} for p in parties],
            'documents': [{'id': d.id, 'name': d.name} for d in docs],
        }

    # ── Activities / Priority No ───────────────────────────────────────────

    @api.model
    def get_priorities(self):
        docs = self.env['pcs.document'].search(
            self._doc_domain(), order='priority_no, name')
        return [{
            'id': d.id,
            'name': d.name,
            'create_date': _d(d.date),
            'delv_date': _d(d.delivery_date),
            'priority_no': d.priority_no,
        } for d in docs]

    @api.model
    def set_priority(self, doc_id, priority_no):
        self.env['pcs.document'].browse(int(doc_id)).priority_no = int(
            priority_no or 0)
        return True

    # ── Activities / Scan station ──────────────────────────────────────────

    @api.model
    def get_scan_config(self):
        Transaction = self.env['pcs.transaction']
        depts = self.env['pcs.department'].search([]).sorted(
            lambda dpt: (dpt.track, dpt.sequence, dpt.code))
        employees = self.env['pcs.employee'].search([('active', '=', True)])
        return {
            'weight_control': Transaction.weight_control_mode(),
            'departments': [{
                'id': dpt.id,
                'code': dpt.code,
                'name': dpt.name,
                'track': dpt.track,
                'is_qc': dpt.is_qc,
                'ask_weight': dpt.auto_weight or dpt.metals or dpt.stones,
                'needs': Transaction._weight_needs(dpt),
            } for dpt in depts],
            'employees': [{
                'id': e.id,
                'code': e.code,
                'name': e.name,
                'department_ids': e.department_ids.ids,
            } for e in employees],
        }

    # ── PCS Settings (operating modes) ─────────────────────────────────────

    @api.model
    def get_pcs_settings(self):
        return {
            'weight_control': self.env['pcs.transaction'].weight_control_mode(),
        }

    @api.model
    def set_pcs_settings(self, values):
        if 'weight_control' in values:
            self.env['pcs.transaction'].set_weight_control_mode(
                values['weight_control'])
        return True

    # ── Activities / SSP ───────────────────────────────────────────────────

    @api.model
    def get_ssp_lookups(self):
        return {
            'ssps': [{'id': s.id, 'name': s.name}
                     for s in self.env['pcs.ssp'].search([], order='code')],
            'employees': [{'id': e.id, 'name': e.name}
                          for e in self.env['pcs.employee'].search(
                              [('active', '=', True)], order='code')],
            'departments': [{'id': d.id, 'name': d.name}
                            for d in self.env['pcs.department'].search(
                                [], order='sequence, code')],
        }

    @api.model
    def get_ssp_transactions(self):
        txns = self.env['pcs.ssp.transaction'].search([], order='id desc')
        return [{
            'id': t.id,
            'ssp': t.ssp_id.name or '',
            'purity': t.purity or '',
            'issue': t.issue_weight,
            'receive': t.receive_weight,
            'date': _d(t.date),
            'by': t.user_id.name or '',
        } for t in txns]

    @api.model
    def report_ssp_consumption(self, month_offset=0):
        """Consumables consumed per worker over a worker month.

        The worker month runs from the 18th to the 17th of the next month
        (the filer receives his wire/blade stock on the 18th and returns
        the leftover at the end): consumed = issued - received.
        """
        from dateutil.relativedelta import relativedelta
        today = fields.Date.context_today(self)
        start = today.replace(day=18)
        if today.day < 18:
            start -= relativedelta(months=1)
        start += relativedelta(months=int(month_offset))
        end = start + relativedelta(months=1)

        txns = self.env['pcs.ssp.transaction'].search([
            ('date', '>=', start), ('date', '<', end)])
        totals = {}
        for txn in txns:
            worker = txn.employee_id.name or (txn.user_id.name or '')
            key = (worker, txn.ssp_id.name or '', txn.purity or '')
            bucket = totals.setdefault(
                key, {'issued': 0.0, 'received': 0.0})
            bucket['issued'] += txn.issue_weight or 0.0
            bucket['received'] += txn.receive_weight or 0.0
        rows = [{
            'worker': worker,
            'ssp': ssp,
            'purity': purity,
            'issued': round(bucket['issued'], 3),
            'received': round(bucket['received'], 3),
            'consumed': round(bucket['issued'] - bucket['received'], 3),
        } for (worker, ssp, purity), bucket in sorted(totals.items())]
        return {
            'start': _d(start),
            'end': _d(end - relativedelta(days=1)),
            'rows': rows,
        }

    @api.model
    def create_ssp_transaction(self, values):
        allowed = {k: v for k, v in values.items() if k in (
            'ssp_id', 'department_id', 'employee_id', 'purity',
            'issue_weight', 'receive_weight')}
        txn = self.env['pcs.ssp.transaction'].create(allowed)
        return txn.id

    # ── Activities / Clearance ─────────────────────────────────────────────

    @api.model
    def get_clearances(self):
        rows = self.env['pcs.clearance'].search([], order='id desc')
        return [{
            'id': c.id,
            'date': _d(c.date),
            'created_by': c.create_uid.name or '',
        } for c in rows]

    @api.model
    def create_clearance(self):
        return self.env['pcs.clearance'].create({}).id

    @api.model
    def get_clearance_lines(self, clearance_id):
        clearance = self.env['pcs.clearance'].browse(int(clearance_id))
        return {
            'prod': [{
                'id': line.id,
                'employee': line.employee_id.name or '',
                'barcode': line.barcode_id.name or '',
                'design': line.design or '',
                'purity': line.purity or '',
                'issue_weight': line.issue_weight,
                'rm_weight': line.rm_weight,
                'received_weight': line.received_weight,
            } for line in clearance.prod_line_ids],
            'ssp': [{
                'id': line.id,
                'employee': line.employee_id.name or '',
                'ssp': line.ssp_id.name or '',
                'purity': line.purity or '',
                'issue_weight': line.issue_weight,
                'received_weight': line.received_weight,
                'date': _d(line.date),
            } for line in clearance.ssp_line_ids],
        }

    # ── Operations timeline ────────────────────────────────────────────────

    @api.model
    def get_timeline(self, document_id=None, barcode_name=None):
        """Chronological chain of operations, per piece.

        Returns one entry per barcode with its ordered transactions (both
        tracks), so the UI can draw the journey of each piece through the
        factory and the raw event log below it.
        """
        Barcode = self.env['pcs.barcode']
        domain = []
        if document_id:
            domain.append(('document_id', '=', int(document_id)))
        if barcode_name:
            cleaned = Barcode.clean_scanned_value(barcode_name)
            domain.append(('name', 'ilike', cleaned))
        if not domain:
            return {'barcodes': []}
        barcodes = Barcode.search(domain, order='document_id desc, line_no')

        result = []
        for barcode in barcodes:
            steps = []
            txns = barcode.transaction_ids.sorted(lambda t: (
                t.issue_date or t.create_date, t.id))
            for txn in txns:
                duration_min = 0
                if txn.issue_date and txn.receive_date:
                    duration_min = int((txn.receive_date - txn.issue_date)
                                       .total_seconds() // 60)
                steps.append({
                    'id': txn.id,
                    'dept_code': txn.department_id.code,
                    'dept_name': txn.department_id.name,
                    'track': txn.department_id.track,
                    'is_qc': txn.department_id.is_qc,
                    'status': txn.status,
                    'worker': txn.employee_id.name or '',
                    'issue_date': _dt(txn.issue_date),
                    'receive_date': _dt(txn.receive_date),
                    'issue_weight': txn.issue_weight,
                    'receive_weight': txn.receive_weight,
                    'issue_stone_weight': txn.issue_stone_weight,
                    'receive_stone_weight': txn.receive_stone_weight,
                    'note': txn.note or '',
                    'duration_min': duration_min,
                })
            result.append({
                'id': barcode.id,
                'barcode': barcode.name,
                'design': barcode.design or '',
                'qty': barcode.qty,
                'steps': steps,
            })
        return {'barcodes': result}

    # ── Reports ────────────────────────────────────────────────────────────

    @api.model
    def report_multi(self, department_id, employee_id=None):
        domain = [('department_id', '=', int(department_id))]
        if not self._sim_included():
            domain.append(('document_id.simulated', '=', False))
        if employee_id:
            domain.append(('employee_id', '=', int(employee_id)))
        txns = self.env['pcs.transaction'].search(domain, order='id')
        cutting, filling = [], []
        for txn in txns:
            barcode = txn.barcode_id
            pcs = int(barcode.qty) or 1
            cutting.append({
                'issued': _dt(txn.issue_date),
                'received': _dt(txn.receive_date),
                'order': barcode.document_id.name,
                'ref': barcode.name,
                'pcs': pcs,
                'i_weight': txn.issue_weight,
                'r_weight': txn.receive_weight,
                'avg': round(txn.receive_weight / pcs, 3)
                       if txn.receive_weight else 0.0,
            })
            fraction = _purity_fraction(barcode.purity)
            total_min = 0
            if txn.issue_date and txn.receive_date:
                total_min = int(
                    (txn.receive_date - txn.issue_date).total_seconds() // 60)
            diff = (txn.issue_weight or 0.0) - (txn.receive_weight or 0.0)
            filling.append({
                'order': barcode.document_id.name,
                'model': barcode.model_code or '',
                'gold': barcode.purity or '',
                'give_time': _dt(txn.issue_date),
                'recv_time': _dt(txn.receive_date),
                'total_min': total_min,
                'given_wt': txn.issue_weight,
                'given_wt_100': round((txn.issue_weight or 0) * fraction, 3),
                'recv_wt': txn.receive_weight,
                'recv_wt_100': round((txn.receive_weight or 0) * fraction, 3),
                'diff_wt': round(diff, 3),
                'diff_wt_100': round(diff * fraction, 3),
            })
        return {'cutting': cutting, 'filling': filling}

    @api.model
    def report_doc_items_dept_cost(self):
        rows = []
        barcodes = self._active_barcodes()
        for barcode in barcodes.sorted(lambda b: (b.document_id.name or '',
                                                  b.line_no)):
            counts = {}
            for txn in barcode.transaction_ids:
                code = txn.department_id.code
                key = 'wip' if txn.status == 'wip' else 'fin'
                counts.setdefault(code, {'wip': 0, 'fin': 0})
                counts[code][key] += 1
            design = barcode.design or ''
            colors = ''
            if '-' in design:
                colors = design.split('-', 1)[1].rsplit('/', 1)[0]
            row = {
                'due_date': _d(barcode.document_id.delivery_date),
                'doc_name': barcode.document_id.name,
                'design': barcode.model_code or '',
                'stone_detail': colors,
                'gold': barcode._metal_letter(),
                'kt': barcode.purity or '',
                'ref': barcode.name,
                'metal_weight': round(barcode._gold_weight(), 3),
            }
            for column, code in DEPT_COST_COLUMNS:
                dept_counts = counts.get(code, {'wip': 0, 'fin': 0})
                row['in_%s' % column] = dept_counts['wip']
                row[column] = dept_counts['fin']
            row['in_qc_final'] = counts.get('QC8', {}).get('wip', 0)
            rows.append(row)
        return rows

    @api.model
    def report_doc_items_finish(self):
        rows = []
        barcodes = self._active_barcodes()
        latest = self._latest_track_txns(barcodes)
        for barcode in barcodes:
            txn = latest.get((barcode.id, 'prod'))
            if not (txn and txn.status == 'fin'
                    and txn.department_id.code == 'FIN'):
                continue
            rows.append({
                'doc_name': barcode.document_id.name,
                'design': barcode.design or '',
                'barcode': barcode.name,
                'gold_id': barcode.metal_code or '',
                'qty': barcode.qty,
                'updated_date': _d(txn.receive_date
                                   and txn.receive_date.date()),
            })
        return rows

    @api.model
    def report_priorities(self, mode='assorted'):
        barcodes = self._active_barcodes()
        latest = self._latest_track_txns(barcodes)

        top = []
        for barcode in barcodes:
            doc = barcode.document_id
            if not (barcode.priority or doc.priority_no):
                continue
            txn = (latest.get((barcode.id, 'prod'))
                   or latest.get((barcode.id, 'stone')))
            top.append({
                'barcode': barcode.name,
                'cur_dept_name': txn.department_id.name if txn else '',
                'delv_date': _d(doc.delivery_date),
                'priority_no': doc.priority_no,
            })
        top.sort(key=lambda r: (r['priority_no'] or 999999, r['barcode']))

        bottom = []
        for barcode in barcodes:
            dept_codes = barcode.transaction_ids.mapped('department_id.code')
            no_cast = 'CST' not in dept_codes
            no_assort = 'AST' not in dept_codes
            no_shaping = 'SHP' not in dept_codes
            assorted = any(
                t.department_id.code == 'AST' and t.status == 'fin'
                for t in barcode.transaction_ids)
            casted = any(
                t.department_id.code == 'CST' and t.status == 'fin'
                for t in barcode.transaction_ids)
            if mode == 'assorted' and not (assorted and no_cast):
                continue
            if mode == 'casted' and not (casted and no_shaping):
                continue
            prod = latest.get((barcode.id, 'prod'))
            stone = latest.get((barcode.id, 'stone'))
            bottom.append({
                'barcode': barcode.name,
                'prod_dept': prod.department_id.name if prod else '',
                'prod_status': ('WIP' if prod.status == 'wip' else 'FIN')
                               if prod else '',
                'stone_dept': stone.department_id.name if stone else '',
                'stone_status': ('WIP' if stone.status == 'wip' else 'FIN')
                                if stone else '',
                'no_cast': no_cast,
                'no_assort': no_assort,
            })
        return {'top': top, 'bottom': bottom}

    @api.model
    def report_sis_not_in_pcs(self):
        in_pcs = self.env['pcs.document'].with_context(
            active_test=False).search([]).mapped('sis_document_id').ids
        docs = self.env['sis.document'].search([
            ('doc_type_code', '=', 'SO'),
            ('id', 'not in', in_pcs),
            ('closed', '=', False),
            ('canceled', '=', False),
        ], order='name desc')
        rows = []
        for doc in docs:
            items = doc.item_ids
            if not items:
                rows.append({'doc_name': doc.name, 'design': ''})
            for item in items:
                rows.append({'doc_name': doc.name,
                             'design': item.design or ''})
        return rows

    @api.model
    def report_order_parts(self, document_id=None, party_id=None):
        docs = self.env['pcs.document'].search(self._doc_domain())
        if document_id:
            docs = docs.filtered(lambda d: d.id == int(document_id))
        if party_id:
            docs = docs.filtered(
                lambda d: d.sis_document_id.party_id.id == int(party_id))
        rows = []
        for doc in docs:
            for barcode in doc.barcode_ids:
                product = barcode.product_id
                if not product:
                    continue
                for part_line in product.part_ids:
                    rows.append({
                        'order': doc.name,
                        'part_id': part_line.part_id.code or '',
                        'part': part_line.part_id.name or '',
                        'qty': (part_line.quantity or 0) * (barcode.qty or 1),
                    })
        return rows

    @api.model
    def report_wax_pdp_weight(self):
        barcodes = self._active_barcodes()
        latest = self._latest_track_txns(barcodes)
        rows = []
        for barcode in barcodes:
            txn = latest.get((barcode.id, 'prod'))
            in_wax = txn and txn.department_id.code == 'WAX'
            not_started = txn is None
            if not (in_wax or not_started):
                continue
            rows.append({
                'barcode': barcode.name,
                'qty': barcode.qty,
                'pdp_weight': round(barcode._gold_weight(), 3),
            })
        return rows

    @api.model
    def report_dashboard_summary(self):
        rows = []
        for doc in self.env['pcs.document'].search(self._doc_domain(),
                                                   order='name'):
            latest = self._latest_track_txns(doc.barcode_ids)
            counts = {}
            for txn in latest.values():
                code = txn.department_id.code
                counts.setdefault(code, 0)
                if txn.status == 'wip':
                    counts[code] += int(txn.barcode_id.qty) or 1
            row = {
                'order_date': _d(doc.date),
                'priority': doc.priority_no,
                'sales_order': doc.name,
                'total': int(doc.total_qty),
                'delivery_date': _d(doc.delivery_date),
            }
            for column, code in SUMMARY_COLUMNS:
                row[column] = counts.get(code, 0)
            rows.append(row)
        return rows
