from odoo import fields, models, tools


class RubiconAlert(models.Model):
    """Operational alerts, computed live from a SQL view — no cron, no mail.

    Thresholds are `ir.config_parameter` keys read at query time, so changing
    them needs no module upgrade (System Parameters):

      rubicon_alert.wip_days               stuck-WIP age, days (default 7)
      rubicon_alert.unscanned_days         barcode never scanned, days (default 7)
      rubicon_alert.rate_days              currency rate unchanged, days (default 30)
      rubicon_alert.overdue_horizon_days   ignore documents due before this
                                           horizon, days (default 180) — keeps
                                           decades of legacy orders out
    """
    _name = 'rubicon.alert'
    _description = 'Rubicon operational alerts'
    _auto = False
    _order = 'days desc'

    alert_type = fields.Selection([
        ('overdue_document', 'Order past due'),
        ('stuck_wip', 'WIP stuck in a department'),
        ('never_scanned', 'Barcode never scanned'),
        ('stale_rate', 'Currency rate not updated'),
    ], readonly=True)
    name = fields.Char(string='Alert', readonly=True)
    date = fields.Date(string='Since', readonly=True)
    days = fields.Integer(string='Days', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'rubicon_alert')
        self.env.cr.execute("""
CREATE VIEW rubicon_alert AS (
WITH params AS (
    SELECT
        COALESCE((SELECT value FROM ir_config_parameter
                   WHERE key = 'rubicon_alert.wip_days'), '7')::int AS wip_days,
        COALESCE((SELECT value FROM ir_config_parameter
                   WHERE key = 'rubicon_alert.unscanned_days'), '7')::int AS unscanned_days,
        COALESCE((SELECT value FROM ir_config_parameter
                   WHERE key = 'rubicon_alert.rate_days'), '30')::int AS rate_days,
        COALESCE((SELECT value FROM ir_config_parameter
                   WHERE key = 'rubicon_alert.overdue_horizon_days'), '180')::int AS overdue_horizon
)
SELECT 10000000 + d.id AS id,
       'overdue_document' AS alert_type,
       d.name || ' - due ' || to_char(d.date_due, 'DD/MM/YYYY') AS name,
       d.date_due AS date,
       (CURRENT_DATE - d.date_due)::int AS days
  FROM sis_document d, params p
 WHERE d.doc_type_code = 'SO'
   AND NOT COALESCE(d.closed, false) AND NOT COALESCE(d.canceled, false)
   AND d.date_due < CURRENT_DATE
   AND d.date_due >= CURRENT_DATE - p.overdue_horizon
UNION ALL
SELECT 20000000 + t.id,
       'stuck_wip',
       t.pbarcode || ' - in ' || dep.name || ' since ' || to_char(t.issue_date, 'DD/MM/YYYY'),
       t.issue_date::date,
       EXTRACT(day FROM now() - t.issue_date)::int
  FROM pcs_transaction t
  JOIN pcs_department dep ON dep.id = t.department_id, params p
 WHERE t.status = 'wip'
   AND t.issue_date < now() - (p.wip_days || ' days')::interval
UNION ALL
SELECT 30000000 + b.id,
       'never_scanned',
       b.name || ' - no scan since the document entered production',
       pd.create_date::date,
       EXTRACT(day FROM now() - pd.create_date)::int
  FROM pcs_barcode b
  JOIN pcs_document pd ON pd.id = b.document_id, params p
 WHERE pd.active
   AND pd.create_date < now() - (p.unscanned_days || ' days')::interval
   AND NOT EXISTS (SELECT 1 FROM pcs_transaction t WHERE t.barcode_id = b.id)
UNION ALL
SELECT 40000000 + c.id,
       'stale_rate',
       cur.name || ' rate unchanged since ' || to_char(last.d, 'DD/MM/YYYY'),
       last.d::date,
       EXTRACT(day FROM now() - last.d)::int
  FROM pdp_currency_setting c
  JOIN res_currency cur ON cur.id = c.currency_id
  CROSS JOIN params p
  CROSS JOIN LATERAL (
      SELECT COALESCE(
          (SELECT max(l.date) FROM rubicon_audit_log l
            WHERE l.model_name = 'pdp.currency.setting'
              AND l.res_id = c.id AND l.field_name = 'rate'),
          c.write_date, c.create_date) AS d
  ) AS last
 WHERE c.active
   AND last.d < now() - (p.rate_days || ' days')::interval
)""")
