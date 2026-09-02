from odoo.addons.pcs_document.tests.test_pcs_document import PcsDocumentCase


class TestRubiconAlerts(PcsDocumentCase):
    """Each alert branch of the SQL view fires on its condition and obeys
    the ir.config_parameter thresholds (read at query time)."""

    def _alerts(self, alert_type):
        # The view reads committed-in-transaction SQL state: push pending ORM
        # writes down before querying it.
        self.env.flush_all()
        return self.env['rubicon.alert'].search([('alert_type', '=', alert_type)])

    def _backdate(self, query, params):
        self.env.flush_all()
        self.env.cr.execute(query, params)
        self.env.invalidate_all()

    def _our_overdues(self):
        return [n for n in self._alerts('overdue_document').mapped('name')
                if 'SO-ZZP-25990' in n]

    def test_overdue_document(self):
        self.sis_doc.write({'date_due': '2020-01-01'})
        self.assertFalse(self._our_overdues())  # beyond the default horizon
        self.env['ir.config_parameter'].sudo().set_param(
            'rubicon_alert.overdue_horizon_days', '36500')
        self.assertTrue(self._our_overdues())
        self.sis_doc.write({'closed': True})
        self.assertFalse(self._our_overdues())

    def test_stuck_wip_and_never_scanned(self):
        doc_id = self.env['pcs.document'].create_from_reference('SO-ZZP-25990')
        doc = self.env['pcs.document'].browse(doc_id)
        barcodes = doc.barcode_ids.sorted('line_no')
        # Document entered production 30 days ago and was never scanned
        self._backdate(
            "UPDATE pcs_document SET create_date = now() - interval '30 days' WHERE id = %s",
            (doc.id,))
        unscanned = self._alerts('never_scanned').mapped('name')
        self.assertTrue(any(barcodes[0].name in n for n in unscanned))
        # First barcode scanned into wax 10 days ago and still there
        result = self.env['pcs.transaction'].scan(barcodes[0].name, self.dept_wax.id)
        self._backdate(
            "UPDATE pcs_transaction SET issue_date = now() - interval '10 days' WHERE id = %s",
            (result['transaction_id'],))
        stuck = self._alerts('stuck_wip').mapped('name')
        self.assertTrue(any(barcodes[0].name in n for n in stuck))
        self.assertFalse(any(barcodes[0].name in n
                             for n in self._alerts('never_scanned').mapped('name')))
        # A higher threshold silences it without any upgrade
        self.env['ir.config_parameter'].sudo().set_param('rubicon_alert.wip_days', '60')
        self.assertFalse(any(barcodes[0].name in n
                             for n in self._alerts('stuck_wip').mapped('name')))

    def test_stale_rate_uses_the_change_history(self):
        currency = self.env['res.currency'].create({'name': 'ZZC', 'symbol': 'z'})
        setting = self.env['pdp.currency.setting'].create({
            'currency_id': currency.id, 'rate': 3.14})
        self._backdate(
            "UPDATE pdp_currency_setting SET write_date = now() - interval '90 days' WHERE id = %s",
            (setting.id,))
        self._backdate(
            "UPDATE rubicon_audit_log SET date = now() - interval '90 days' "
            "WHERE model_name = 'pdp.currency.setting' AND res_id = %s", (setting.id,))
        stale = self._alerts('stale_rate').mapped('name')
        self.assertTrue(any('ZZC' in n for n in stale))
        # Updating the rate journals a change, which clears the alert
        setting.write({'rate': 3.15})
        self.assertFalse(any('ZZC' in n for n in self._alerts('stale_rate').mapped('name')))
