"""Offline Vertex composition and cost regression tests; not runtime proof."""
import json
import re
import subprocess
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class VertexTarget(unittest.TestCase):
    def test_native_auth_connection(self):
        root = ET.parse(ROOT / 'assets/examples/target/vertex-connection.xml').getroot()
        self.assertEqual(root.tag, 'HTTPTargetConnection')
        self.assertEqual(root.findtext('Authentication/GoogleAccessToken/Scopes/Scope'),
                         'https://www.googleapis.com/auth/cloud-platform')
        self.assertEqual(root.findtext('URL'), '__VERTEX_CHAT_COMPLETIONS_URL__')
        self.assertIsNone(root.find('Authentication/GoogleIDToken'))

    def test_setup_shell_syntax(self):
        doc = (ROOT / 'references/vertex-target.md').read_text()
        blocks = re.findall(r'```bash\n(.*?)\n```', doc, re.S)
        self.assertTrue(blocks)
        for block in blocks:
            subprocess.run(['bash', '-n'], input=block, text=True, check=True, capture_output=True)
        self.assertIn('gcloud services enable aiplatform.googleapis.com --project="$VERTEX_PROJECT_ID"', doc)
        self.assertIn('gcloud services list --enabled --project="$VERTEX_PROJECT_ID"', doc)

    def test_cost_modes(self):
        # Synthetic usage fixtures exercise arithmetic, not provider behaviour.
        harness = r'''
const fs = require('fs'), vm = require('vm');
const code = fs.readFileSync(process.argv[1], 'utf8');
const cases = JSON.parse(process.argv[2]);
console.log(JSON.stringify(cases.map(c => {
  const vars = {'response.content': JSON.stringify({usage:c.usage}),
    'ai.alias':'fast',
    'verifyapikey.VAK.apiproduct.price_input_per_1m_fast':'2',
    'verifyapikey.VAK.apiproduct.price_output_per_1m_fast':'3'};
  vm.runInNewContext(code, {properties:{verifyApiKeyPolicy:'VAK',
    modelAliasVariable:'ai.alias', usageMode:c.mode}, context:{
      getVariable:k => vars[k], setVariable:(k,v) => {vars[k]=v;}}});
  return [vars['cost.valid'], vars['cost.microusd']];
})));
'''
        vertex = 'vertex-total-minus-prompt'
        cases = [
            ({'prompt_tokens':3, 'completion_tokens':3, 'total_tokens':63,
              'completion_tokens_details':{'reasoning_tokens':57}}, vertex, ['true','186']),
            # Reasoning already included in completion: never add it twice.
            ({'prompt_tokens':3, 'completion_tokens':60, 'total_tokens':63,
              'completion_tokens_details':{'reasoning_tokens':57}}, vertex, ['true','186']),
            ({'prompt_tokens':3, 'completion_tokens':3}, None, ['true','15']),
            ({'prompt_tokens':3, 'completion_tokens':3}, 'completion', ['true','15']),
            ({'prompt_tokens':0, 'completion_tokens':0, 'total_tokens':0}, vertex, ['true','0']),
            ({'prompt_tokens':3, 'completion_tokens':3}, vertex, ['false','0']),
            ({'prompt_tokens':3, 'completion_tokens':3, 'total_tokens':5}, vertex, ['false','0']),
            ({'prompt_tokens':3, 'completion_tokens':3, 'total_tokens':-1}, vertex, ['false','0']),
            ({'prompt_tokens':3, 'completion_tokens':3, 'total_tokens':6.5}, vertex, ['false','0']),
            ({'prompt_tokens':3, 'completion_tokens':3, 'total_tokens':'63'}, vertex, ['false','0']),
            ({'prompt_tokens':None, 'completion_tokens':3, 'total_tokens':63}, vertex, ['false','0']),
            ({'prompt_tokens':3, 'completion_tokens':3}, 'unknown', ['false','0']),
        ]
        payload = [{'usage':u, 'mode':m} for u,m,_ in cases]
        result = subprocess.run(['node', '-e', harness,
            str(ROOT / 'assets/examples/cost-budget/calculate-cost.js'), json.dumps(payload)],
            text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), [expected for _,_,expected in cases])


if __name__ == '__main__':
    unittest.main()
