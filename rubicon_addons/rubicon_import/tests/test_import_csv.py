import tempfile
import os
import csv

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from ..import_scripts.generic import import_csv


class TestCSVImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))

        # Création d'une catégorie de test pour le many2one
        self.category = self.env['pdp.stone.category'].create(
            {'code':'CAT1', 'name': 'TestCat'}
            )

        # Création d'un fichier CSV temporaire
        self.tmpdir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.tmpdir.name, 'pdp.stone.type.csv')

        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['xml_id', 'code', 'name', 'density', 'category_code'])
            writer.writerow(['TEST_1_xml_id', 'TES1', 'Test 1', '1.23', 'CAT1'])


    @mute_logger('odoo.models')
    def test_import_csv_creates_stone_type(self):
        model = self.env['pdp.stone.type']
        logs = import_csv(
            self.env, model,
            csv_path=self.csv_path,  # 👈 on injecte le chemin vers le fichier temporaire
            module='pdp_stone',  # nécessaire pour le xml_id
            verbose=False,
            register_xml_id=True
        )
        print(logs)
        stone = self.env.ref('pdp_stone.TEST_1_xml_id', raise_if_not_found=False)
        self.assertTrue(stone)
        self.assertEqual(stone.name, 'Test 1')
        self.assertEqual(stone.category_code.name, 'TestCat')
        self.assertEqual(logs['created'], 1)
        self.assertEqual(logs['skipped'], 0)

    def tearDown(self):
        self.tmpdir.cleanup()
        stone = self.env.ref('pdp_stone.TEST_1_xml_id', raise_if_not_found=False)
        if stone:
            stone.unlink()
        self.category.unlink()
        super().tearDown()
