"""
Standalone tests for the SIS party/document converter (raw_to_data_sis.py).

Reference records from meta/sis/main_with_example.md:
  - Party: A&J INTERNATIONAL (ID=7)
  - Document: SO-EMA-25001 (legacy_id=13159)
  - Item: P720-RHO+LAM+GT+PT/P on SO-EMA-25001

Run: python -m pytest rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py -v
"""
import os
import csv
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from rubicon_import.raw_to_data.raw_to_data_sis import (
    build_lookups, make_row_to_party, make_row_to_document, make_row_to_doc_item,
    s, clean_phone,
)

_BACKUP = os.path.join(os.path.dirname(__file__), '../../../data/backup_sis')

def _party_row(pid: str):
    path = os.path.join(_BACKUP, 'CustomersJoined.csv')
    with open(path, encoding='utf-8') as f:
        for row in csv.reader(f):
            if row and s(row[0]) == pid:
                return row
    return None


def _doc_row(doc_name: str):
    path = os.path.join(_BACKUP, 'SalesDocs.csv')
    with open(path, encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) > 3 and s(row[3]) == doc_name:
                return row
    return None


def _item_rows(doc_type: str, legacy_id: int):
    path = os.path.join(_BACKUP, 'SalesDocItems.csv')
    rows = []
    with open(path, encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) > 4 and s(row[0]) == doc_type and s(row[1]) == str(legacy_id):
                rows.append(row)
    return rows


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

    def test_ship_name_is_care_of(self):
        # delivery.name = addressee / care-of (first address line)
        assert 'sis_ship_name' in self.company
        assert self.company['sis_ship_name'] == 'KLEX CORPORATION'

    def test_ship_street_is_main_street(self):
        assert 'sis_ship_street' in self.company
        assert '7905' in self.company['sis_ship_street']

    def test_ship_street2_is_complement(self):
        # street2 = suite / complement, not the care-of name
        assert 'sis_ship_street2' in self.company
        assert self.company['sis_ship_street2'] == 'Suite 601'

    def test_ship_city_in_csv(self):
        assert 'sis_ship_city' in self.company
        assert self.company['sis_ship_city'] == 'MIAMI'

    def test_ship_zip_in_csv(self):
        assert 'sis_ship_zip' in self.company
        assert self.company['sis_ship_zip'] == '33143'

    def test_ship_country_in_csv(self):
        assert 'sis_ship_country_id' in self.company
        assert self.company['sis_ship_country_id'] == 'United States'

    def test_state_code_exported(self):
        assert 'state_code' in self.company
        assert self.company['state_code'] == 'FL'

    def test_ship_state_code_exported(self):
        assert 'sis_ship_state_code' in self.company
        assert self.company['sis_ship_state_code'] == 'FL'

    # ── bank info (ref: main_with_example.md § Bank Info) ────────────────────

    def test_bank_name(self):
        assert 'bank_name' in self.company
        assert self.company['bank_name'] == 'NEUFLIZE OBC Enterprises'

    def test_bank_acc_no(self):
        assert 'bank_acc_no' in self.company
        assert 'FR35 1497' in self.company['bank_acc_no']

    def test_bank_acc_name(self):
        assert 'bank_acc_name' in self.company
        assert 'BIC' in self.company['bank_acc_name']

    def test_bank_address_non_empty(self):
        assert 'bank_address' in self.company
        assert 'Hoche' in self.company['bank_address']

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


# ─── SO-EMA-25001 (document) ──────────────────────────────
# Reference from meta/sis/main_with_example.md § Required Field + General

class TestDocumentSOEMA25001:
    """
    Reference: SO-EMA-25001, legacy_id=13159.
    Covers all documented fields from main_with_example.md.
    footnotes not tested (documented as excluded).
    """

    def setup_method(self):
        lookups = build_lookups()
        converter = make_row_to_document(lookups)
        row = _doc_row('SO-EMA-25001')
        assert row is not None, "SO-EMA-25001 not found in SalesDocs.csv"
        self.doc = converter(row)
        assert self.doc is not None, "Converter returned None for SO-EMA-25001"

    # ── identity ──────────────────────────────────────────

    def test_xml_id(self):
        assert self.doc['id'] == 'sis_doc_SO_13159'

    def test_name(self):
        assert self.doc['name'] == 'SO-EMA-25001'

    def test_doc_type_code(self):
        assert self.doc['doc_type_code'] == 'SO'

    def test_legacy_id(self):
        assert self.doc['legacy_id'] == 13159

    # ── header fields ─────────────────────────────────────

    def test_date_created(self):
        assert self.doc['date_created'] == '2025-01-06'

    def test_date_due(self):
        assert self.doc['date_due'] == '2025-01-31'

    def test_closed_is_true(self):
        assert self.doc['closed'] is True

    def test_canceled_is_false(self):
        assert self.doc['canceled'] is False

    # ── general tab fields ────────────────────────────────

    def test_party_id_resolves_to_emasur(self):
        assert self.doc['party_id'] == 'EMASUR'

    def test_stamp(self):
        assert self.doc['stamp'] == 'EMA+IL'

    def test_customer_po(self):
        assert self.doc['customer_po'] == '#8001'

    def test_ship_method_resolves_to_courier(self):
        assert self.doc['ship_method_id'] == 'Courier'

    def test_pay_term_resolves_to_tt(self):
        assert self.doc['pay_term_id'] == 'T/T'

    def test_employee(self):
        assert self.doc['employee'] == 'ORM'

    def test_rcv_mode_resolves_to_email(self):
        assert self.doc['rcv_mode_id'] == 'Email'

    def test_notes(self):
        assert self.doc['notes'] == 'Gold : 2645$'

    # ── financials ────────────────────────────────────────

    def test_currency(self):
        assert self.doc['currency'] == 'US'

    def test_total_qty(self):
        assert self.doc['total_qty'] == 1

    def test_total_fob(self):
        assert self.doc['total_fob'] == 195.0

    def test_freight_insurance(self):
        assert self.doc['freight_insurance'] == 0.0

    def test_total_cif(self):
        assert self.doc['total_cif'] == 195.0

    def test_total_cost(self):
        assert self.doc['total_cost'] == 118.03

    def test_total_profit(self):
        assert self.doc['total_profit'] == 76.97

    # ── forbidden fields ──────────────────────────────────

    def test_no_margin_name_field(self):
        assert 'margin_name' not in self.doc


# ─── P720-RHO+LAM+GT+PT/P on SO-EMA-25001 (item) ─────────
# Reference from meta/sis/main_with_example.md § Items/*

class TestItemP720OnSOEMA25001:
    """
    Reference: single item P720-RHO+LAM+GT+PT/P on SO-EMA-25001.
    Covers General, Instructions, Sizes, Weights and Profit sub-tabs.
    """

    def setup_method(self):
        converter = make_row_to_doc_item()
        item_rows = _item_rows('SO', 13159)
        assert item_rows, "No items found for SO/13159 in SalesDocItems.csv"
        items = [r for r in item_rows if s(r[4]) == 'P720-RHO+LAM+GT+PT/P']
        assert items, "P720-RHO+LAM+GT+PT/P not found among SO-EMA-25001 items"
        self.item = converter(items[0])
        assert self.item is not None

    # ── General ───────────────────────────────────────────

    def test_design(self):
        assert self.item['design'] == 'P720-RHO+LAM+GT+PT/P'

    def test_purity(self):
        assert self.item['purity'].strip() == '18K'

    def test_qty(self):
        assert self.item['qty'] == 1.0

    def test_unit_price(self):
        assert self.item['unit_price'] == 195.0

    def test_amount(self):
        assert self.item['amount'] == 195.0

    def test_description(self):
        assert '12 MM' in self.item['description']
        assert 'LTSA' in self.item['description']

    # ── Instructions ──────────────────────────────────────

    def test_item_group(self):
        assert '#8001' in self.item['item_group']
        assert 'ADC' in self.item['item_group']

    def test_special_instruction(self):
        assert '12 MM' in self.item['special_instruction']
        assert 'LTSA' in self.item['special_instruction']

    # ── Sizes ─────────────────────────────────────────────

    def test_size_remarks_empty(self):
        assert self.item['size_remarks'] == ''

    # ── Weights ───────────────────────────────────────────

    def test_diamond_weight_zero(self):
        assert self.item['diamond_weight'] == 0.0

    def test_stone_weight_zero(self):
        assert self.item['stone_weight'] == 0.0

    def test_diverse_weight_zero(self):
        assert self.item['diverse_weight'] == 0.0

    def test_metal_weight(self):
        assert self.item['metal_weight'] == 1.1

    # ── Profit ────────────────────────────────────────────

    def test_unit_cost(self):
        assert self.item['unit_cost'] == 118.03

    def test_cost(self):
        assert self.item['cost'] == 118.03

    def test_profit(self):
        assert self.item['profit'] == 76.97

    def test_profit_pct_cost_based(self):
        # 76.97 / 118.03 = 65.21% (cost-based, not revenue-based)
        assert abs(self.item['profit_pct'] - 0.6521) < 0.001
