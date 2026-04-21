"""
Standalone tests for the SIS party/document converter (raw_to_data_sis.py).

Reference record: A&J INTERNATIONAL (party ID=7) from meta/sis/main_with_example.md
Run: python -m pytest rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py -v
"""
import os
import csv
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from rubicon_import.raw_to_data.raw_to_data_sis import (
    build_lookups, make_row_to_party, s, clean_phone,
)

_BACKUP = os.path.join(os.path.dirname(__file__), '../../../data/backup_sis')


def _party_row(pid: str):
    path = os.path.join(_BACKUP, 'CustomersJoined.csv')
    with open(path, encoding='utf-8') as f:
        for row in csv.reader(f):
            if row and s(row[0]) == pid:
                return row
    return None


# ─── clean_phone ──────────────────────────────────────────

class TestCleanPhone:
    def test_strips_leading_space(self):
        assert clean_phone(' 52 333 121 3410') == '52 333 121 3410'

    def test_keeps_internal_spaces(self):
        assert clean_phone('52 333 641 1423') == '52 333 641 1423'

    def test_empty_returns_empty(self):
        assert clean_phone('') == ''

    def test_null_byte_cleaned(self):
        assert clean_phone('\x0052 333') == '52 333'


# ─── A&J INTERNATIONAL (party 7) ──────────────────────────

class TestParty7AJ:
    """
    Reference from meta/sis/main_with_example.md — A&J INTERNATIONAL.
    Every assertion maps directly to a documented field value.
    """

    def setup_method(self):
        lookups = build_lookups()
        converter = make_row_to_party(lookups)
        row = _party_row('7')
        assert row is not None, "Party 7 not found in CustomersJoined.csv"
        self.records = list(converter(row))
        assert self.records, "Converter produced no records for party 7"
        self.company = self.records[0]

    # ── identity ──────────────────────────────────────────

    def test_xml_id(self):
        assert self.company['id'] == 'sis_party_7'

    def test_sis_code(self):
        # field name must be sis_code (not 'code')
        assert 'sis_code' in self.company
        assert self.company['sis_code'] == 'A&J'

    def test_name(self):
        # field name must be 'name' (not 'company')
        assert 'name' in self.company
        assert self.company['name'] == 'A&J INTERNATIONAL'

    def test_active(self):
        assert self.company['active'] is True

    def test_is_company(self):
        assert self.company['is_company'] is True

    # ── customer / vendor ─────────────────────────────────

    def test_sis_is_customer(self):
        assert 'sis_is_customer' in self.company
        assert self.company['sis_is_customer'] is True

    def test_sis_is_vendor(self):
        assert 'sis_is_vendor' in self.company
        assert self.company['sis_is_vendor'] is False

    def test_customer_rank(self):
        assert self.company['customer_rank'] == 1

    def test_supplier_rank(self):
        assert self.company['supplier_rank'] == 0

    # ── address ───────────────────────────────────────────

    def test_street_contains_street_address(self):
        assert '7905 S.W. 86 STREET SUITE 601' in self.company['street']

    def test_city(self):
        assert self.company['city'] == 'MIAMI'

    def test_zip(self):
        assert self.company['zip'] == '33143'

    def test_country_id_is_odoo_name(self):
        # Must use Odoo res.country name, not sis_country_XX external id
        assert self.company['country_id'] == 'United States'

    def test_no_sis_country_reference(self):
        # Odoo res.partner.country_id is M2O to res.country — never sis.country
        assert 'country_id/id' not in self.company or not str(self.company.get('country_id/id', '')).startswith('sis_country_')

    # ── contact ───────────────────────────────────────────

    def test_phone_readable(self):
        # Spaces must be kept; leading space trimmed
        assert self.company['phone'] == '52 333 121 3410'

    def test_mobile_second_phone(self):
        # Second phone line must be captured
        assert 'mobile' in self.company
        assert self.company['mobile'] == '52 333 641 1423'

    def test_email_no_mailto_prefix(self):
        assert self.company['email'] == 'coloradojr@gmail.com'

    def test_notes_contain_mobile(self):
        assert 'mobile 089-0440321' in self.company['notes']

    # ── contact name still in CSV (used by sync_parties.py for contact child) ──────

    def test_contact_name_in_csv(self):
        assert self.company['sis_contact'] == 'Mr. Jose V. ROSAS'

    # ── defaults ──────────────────────────────────────────

    def test_margin_id_code(self):
        # WHO is the pdp.margin code (_rec_name='code') for Wholesale
        assert 'margin_id' in self.company
        assert self.company['margin_id'] == 'WHO'

    def test_pay_term_by_name(self):
        # sis.pay.term matched by name
        assert 'sis_pay_term_id' in self.company
        assert self.company['sis_pay_term_id'] == 'T/T'

    # ── shipment ──────────────────────────────────────────

    def test_ship_method_by_name(self):
        # sis.shipper matched by name
        assert 'sis_ship_method_id' in self.company
        assert self.company['sis_ship_method_id'] == 'Courier'

    def test_ship_fedex_acc(self):
        assert 'sis_ship_fedex_acc' in self.company
        assert self.company['sis_ship_fedex_acc'] == 'TEL: 1 305 412 7477 / FAX: 1 305 412 8404'

    def test_ship_stamp(self):
        assert 'sis_ship_stamp' in self.company
        assert self.company['sis_ship_stamp'] == '750 + 2'

    # ── ship data still present in CSV (used by sync_parties.py for delivery child) ───

    def test_ship_city_in_csv(self):
        assert self.company['sis_ship_city'] == 'MIAMI'

    def test_ship_zip_in_csv(self):
        assert self.company['sis_ship_zip'] == '33143'

    def test_ship_country_in_csv(self):
        assert self.company['sis_ship_country_id'] == 'United States'

    def test_ship_state_code_in_csv(self):
        assert self.company['sis_ship_state_code'] == 'FL'

    def test_state_code_exported(self):
        assert 'state_code' in self.company
        assert self.company['state_code'] == 'FL'

    def test_ship_state_code_exported(self):
        assert 'sis_ship_state_code' in self.company
        assert self.company['sis_ship_state_code'] == 'FL'

    # ── removed / forbidden fields ────────────────────────

    def test_no_contact_type_field(self):
        # contact_type is not a res.partner field
        assert 'contact_type' not in self.company

    def test_no_fax_field(self):
        # fax removed from res.partner in Odoo 18
        assert 'fax' not in self.company

    def test_no_group_code_field(self):
        # renamed to margin_id
        assert 'group_code' not in self.company

    def test_no_old_pay_term_field(self):
        assert 'pay_term_id' not in self.company

    def test_no_old_ship_method_field(self):
        assert 'ship_method_id' not in self.company

    def test_no_old_ship_stamp_field(self):
        assert 'ship_stamp' not in self.company
