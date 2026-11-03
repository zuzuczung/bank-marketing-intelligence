import unittest
from bank_bi.rules import age_band,contact_band,validate_row
from bank_bi.source import COLUMNS


class ContractTests(unittest.TestCase):
    def row(self):
        return dict(zip(COLUMNS,['30','unknown','single','unknown','no','-50','no','no',
             'unknown','1','jan','0','1','-1','0','unknown','no']))

    def test_unknown_negative_balance_and_sentinel_are_valid(self):
        self.assertTrue(validate_row(self.row()))

    def test_missing_outcome_fails(self):
        r=self.row();r['y']=''
        with self.assertRaises(ValueError):validate_row(r)

    def test_unknown_outcome_fails(self):
        r=self.row();r['y']='unknown'
        with self.assertRaises(ValueError):validate_row(r)

    def test_zero_campaign_fails(self):
        r=self.row();r['campaign']='0'
        with self.assertRaises(ValueError):validate_row(r)

    def test_bad_sentinel_fails(self):
        r=self.row();r['pdays']='-2'
        with self.assertRaises(ValueError):validate_row(r)

    def test_age_boundaries(self):
        self.assertEqual([age_band(n) for n in [29,30,39,40,49,50,59,60]],
            ['01 · Dưới 30','02 · 30–39','02 · 30–39','03 · 40–49','03 · 40–49','04 · 50–59','04 · 50–59','05 · Từ 60'])

    def test_contact_boundaries(self):
        self.assertEqual([contact_band(n)[:2] for n in [1,2,3,4,5,6,10,11]],['01','02','03','04','04','05','05','06'])

    def test_high_outliers_not_removed(self):
        r=self.row();r.update(age='95',duration='5000',campaign='63')
        self.assertTrue(validate_row(r))


if __name__=='__main__':unittest.main()
