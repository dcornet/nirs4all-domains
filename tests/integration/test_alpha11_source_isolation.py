"""Adversarial source adaptation: sealed reference cells never control admission."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from run_alpha11_litter import assemble


class SourceIsolationTests(unittest.TestCase):
    def tables(self):
        rows={}
        for i in range(31):
            s=f'{i}_tree_S_{i}'
            rows[s]={'ID':s,'plot':str(i),'individual':'tree','species':'S','number':str(i),'Nmass':str(i*.1),'400':str(i)}
        return rows,copy.deepcopy(rows)

    def test_sealed_numeric_references_cannot_change_task_or_admission_inputs(self):
        a,b=self.tables();expected=assemble(['400'],a,b);retained=set(expected[2]['retained_groups'])
        for key in a:
            if a[key]['plot'] in retained:
                a[key]['Nmass']='DO_NOT_PARSE';b[key]['Nmass']='A_DIFFERENT_FORBIDDEN_VALUE'
        self.assertEqual(expected,assemble(['400'],a,b))

    def test_development_reference_contradictions_still_block(self):
        a,b=self.tables();retained=set(assemble(['400'],a,b)[2]['retained_groups'])
        key=next(k for k in a if a[k]['plot'] not in retained);b[key]['Nmass']='different'
        with self.assertRaisesRegex(ValueError,'DEVELOPMENT_REFERENCE_CONTRADICTION'):assemble(['400'],a,b)

    def test_retained_physical_identity_contradictions_still_block_without_y(self):
        a,b=self.tables();retained=set(assemble(['400'],a,b)[2]['retained_groups'])
        key=next(k for k in a if a[k]['plot'] in retained);b[key]['individual']='other'
        with self.assertRaisesRegex(ValueError,'METADATA_OR_REFERENCE'):assemble(['400'],a,b)


if __name__=='__main__':unittest.main()
