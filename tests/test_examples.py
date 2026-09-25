"""Local structural checks only; not Apigee schema or runtime qualification."""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from doc_checks import check_examples, check_links, markdown_documents, markdown_links

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets/examples'

# Explicit example coverage: never derive expected results from discovered
# markers or XML files. Three additional assets are intentionally linked-only.
EXPECTED_EXAMPLES = {
    'assets/examples/target/AM-PrepareTargetRequest.xml',
    'assets/examples/target/target-request-flow.xml',
    'assets/examples/token-quota/LTQ-Enforce.xml',
    'assets/examples/token-quota/LTQ-Count.xml',
    'assets/examples/token-quota/proxy-flow-fragment.xml',
    'assets/examples/cost-budget/LTQ-CostEnforce.xml',
    'assets/examples/cost-budget/JS-CalculateCost.xml',
    'assets/examples/cost-budget/LTQ-CostCount.xml',
    'assets/examples/cost-budget/proxy-flow-fragment.xml',
    'assets/examples/model-armor/EV-ArmorPrompt.xml',
    'assets/examples/model-armor/EV-ArmorResponse.xml',
    'assets/examples/model-armor/SUP-InspectPrompt.xml',
    'assets/examples/model-armor/SMR-InspectResponse.xml',
    'assets/examples/model-armor/RF-ArmorIncomplete.xml',
    'assets/examples/model-armor/JS-ValidateArmorPrompt.xml',
    'assets/examples/model-armor/JS-ValidateArmorResponse.xml',
    'assets/examples/model-armor/proxy-flow-fragment.xml',
    'assets/examples/prompt-token-limit/EV-BurstPrompt.xml',
    'assets/examples/prompt-token-limit/PTL-ProtectPromptBurst.xml',
    'assets/examples/prompt-token-limit/proxy-flow-fragment.xml',
    'assets/examples/prompt-token-limit/prompt-limit-fault-fragment.xml',
    'assets/examples/prompt-token-limit/AM-PromptBurstExceeded.xml',
    'assets/examples/semantic-cache/SCL-LookupFAQ.xml',
    'assets/examples/semantic-cache/SCP-PopulateFAQ.xml',
    'assets/examples/semantic-cache/psc-search-fragment.xml',
    'assets/examples/semantic-cache/proxy-flow-fragment.xml',
}
LINKED_ONLY = {
    'assets/examples/target/AM-SetUpstreamAuth.xml',
    'assets/examples/token-quota/AM-QuotaExceeded.xml',
    'assets/examples/token-quota/quota-fault-fragment.xml',
    'assets/examples/cost-budget/RF-CostConfigMissing.xml',
    'assets/examples/cost-budget/cost-budget-fault-fragment.xml',
    'assets/examples/cost-budget/AM-CostBudgetExceeded.xml',
}


def examples_in(folder):
    return [(name, snippet) for name, snippet in check_examples(ROOT, EXPECTED_EXAMPLES).items()
            if Path(name).parent.name == folder]


class Examples(unittest.TestCase):
    def test_all_xml_parses(self):
        files = list(ASSETS.rglob('*.xml'))
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path):
                ET.parse(path)

    def test_links_resolve(self):
        linked = check_links(ROOT, markdown_documents(ROOT))
        self.assertTrue(LINKED_ONLY <= linked, LINKED_ONLY - linked)

    def test_inline_examples_match_assets(self):
        self.assertEqual(set(check_examples(ROOT, EXPECTED_EXAMPLES)), EXPECTED_EXAMPLES)

    def test_asset_coverage(self):
        expected = EXPECTED_EXAMPLES | LINKED_ONLY
        self.assertEqual({p.relative_to(ROOT).as_posix() for p in ASSETS.rglob('*.xml')}, expected)

    def test_region_placeholders_precede_setup_commands(self):
        # Position/placeholder checks; location approval requires semantic review.
        # Discover the command-owning Armor reference so its later split is safe.
        owners = []
        for doc in (ROOT / 'references').rglob('*.md'):
            text = doc.read_text()
            if 'model-armor' in doc.name and '```bash' in text:
                owners.append(doc)
                self.assertIn('__APPROVED_TEMPLATE_LOCATION__', text, doc)
                self.assertLess(text.index('__APPROVED_TEMPLATE_LOCATION__'), text.index('```bash'), doc)
                self.assertIn('__TEMPLATE_LOCATION__', text, doc)
        self.assertTrue(owners, 'Model Armor setup commands missing')

    def test_armor_split_navigation_and_placeholder_contract(self):
        # Structural ownership/order only; review approval and native boundaries separately.
        workflow_path = ROOT / 'references/model-armor.md'
        setup_path = ROOT / 'references/model-armor-setup.md'
        workflow, setup = workflow_path.read_text(), setup_path.read_text()
        self.assertNotIn('```bash', workflow)
        self.assertNotIn('```xml', setup)
        self.assertIn('references/model-armor-setup.md', check_links(ROOT, [workflow_path]))
        self.assertIn('references/model-armor.md', check_links(ROOT, [setup_path]))
        first_xml = workflow.index('```xml')
        for anchor in ['location-gate-before-commands',
                       'reuse-or-create-a-template',
                       'known-limitations',
                       'manual-pre-import-handoff']:
            target = 'model-armor-setup.md#' + anchor
            self.assertLess(workflow.index(target), first_xml, target)
        self.assertLess(workflow.index('__APPROVED_TEMPLATE_LOCATION__'), first_xml)
        self.assertLess(setup.index('__APPROVED_TEMPLATE_LOCATION__'), setup.index('```bash'))
        rows = [line for line in workflow.splitlines() if line.startswith('| `__')]
        documented = set(re.findall(r'__[A-Z_]+__', '\n'.join(
            line.split('|')[1] for line in rows)))
        required = set()
        for _, snippet in examples_in('model-armor'):
            required.update(re.findall(r'__[A-Z_]+__', snippet))
        self.assertEqual(documented, required | {'__APPROVED_TEMPLATE_LOCATION__'})
        for owner in ['README.md', 'SKILL.md', 'references/semantic-cache.md']:
            self.assertIn('references/model-armor-setup.md',
                          check_links(ROOT, [ROOT / owner]), owner)

    def test_no_hardcoded_regions_in_documented_commands(self):
        commands = []
        for doc in markdown_documents(ROOT):
            for block in re.findall(r'```(?:bash|sh|shell)\n(.*?)\n```', doc.read_text(), re.S):
                commands.append(block)
                self.assertNotRegex(block, r'\b(?:us|europe|asia|australia|northamerica|southamerica|africa|me)-[a-z]+\d+\b', doc)
        self.assertTrue(commands)

    def test_readme_feature_navigation(self):
        linked = check_links(ROOT, [ROOT / 'README.md'])
        for name in ['model-routing', 'api-product-setup', 'token-quota', 'cost-budget', 'model-armor', 'prompt-token-limit',
                     'semantic-cache', 'semantic-cache-vertex-setup']:
            self.assertIn('references/' + name + '.md', linked)
        # Review evidence levels, manual-import and independent-review obligations separately.

    def test_readme_ledger_and_six_lab_navigation(self):
        readme = (ROOT / 'README.md').read_text()
        links = markdown_links(readme)
        self.assertIn('references/capability-status.md#current-status', links)
        self.assertIn('references/capability-status.md#what-the-statuses-mean', links)
        # README is the quickstart; each lab lives in its own short page under labs/.
        for number in range(7):
            pages = sorted((ROOT / 'labs').glob(f'lab-{number}-*.md'))
            self.assertEqual(len(pages), 1, f'Lab {number} page')
            page = pages[0]
            self.assertIn('labs/' + page.name, links)
            text = page.read_text()
            self.assertRegex(text, rf'^# Lab {number} — ', page.name)
            self.assertRegex(text, re.compile(r'^## Prompt$', re.M), page.name)
            self.assertTrue(any(link.startswith('../README.md') for link in markdown_links(text)), page.name)
        for target in ['labs/combined-build.md', 'EVALUATION.md', 'lab-config.example.md']:
            self.assertIn(target, links)
        evaluation = markdown_links((ROOT / 'EVALUATION.md').read_text())
        self.assertIn('references/capability-status.md#current-status', evaluation)
        self.assertIn('references/capability-status.md#what-the-statuses-mean', evaluation)
        # Feature status owns the status rows. Check schema and coverage, not wording.
        ledger = (ROOT / 'references/capability-status.md').read_text()
        table = ledger.split('## Current status\n', 1)[1]
        rows = [line.strip('|').split('|') for line in table.splitlines()
                if line.startswith('|')][2:]
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(len(row), 3)
            self.assertTrue(all(cell.strip() for cell in row))
        required = {'Model routing', 'Accumulated token quota', 'Cost budget', 'Model Armor',
                    'Prompt-token burst protection', 'FAQ semantic caching'}
        self.assertTrue(required <= {row[0].strip() for row in rows})

    def test_cost_budget_pairing_and_flow(self):
        folder = ASSETS / 'cost-budget'
        enforce = ET.parse(folder / 'LTQ-CostEnforce.xml').getroot()
        count = ET.parse(folder / 'LTQ-CostCount.xml').getroot()
        self.assertEqual(enforce.findtext('EnforceOnly'), 'true')
        self.assertEqual(count.findtext('CountOnly'), 'true')
        for path in ['SharedName', 'Interval', 'TimeUnit', 'Synchronous', 'Distributed', 'LLMModelSource']:
            self.assertEqual(enforce.findtext(path), count.findtext(path), path)
        for tag in ['Allow', 'Interval', 'TimeUnit', 'Identifier']:
            for attr in ['count', 'countRef', 'ref']:
                self.assertEqual(enforce.find(tag).get(attr), count.find(tag).get(attr), tag + attr)
        self.assertIn('apiproduct.cost_budget_microusd', enforce.find('Allow').get('countRef'))
        self.assertEqual(count.findtext('LLMTokenUsageSource'), '{cost.microusd}')
        self.assertEqual(count.findtext('LLMModelSource'), '{__UPSTREAM_MODEL_VARIABLE__}')
        js = ET.parse(folder / 'JS-CalculateCost.xml').getroot()
        self.assertEqual(js.tag, 'Javascript')
        self.assertEqual(js.findtext('ResourceURL'), 'jsc://calculate-cost.js')
        self.assertTrue((folder / 'calculate-cost.js').is_file())
        flow = ET.parse(folder / 'proxy-flow-fragment.xml').getroot()
        self.assertEqual([x.text for x in flow.findall('Response/Step/Name')],
                         ['JS-CalculateCost', 'LTQ-CostCount'])
        self.assertIn('cost.valid = "true"', flow.findall('Response/Step')[1].findtext('Condition'))
        self.assertIn('references/cost-budget.md',
                      check_links(ROOT, [ROOT / 'SKILL.md', ROOT / 'README.md']))

    def test_armor_native_sources_and_capture(self):
        folder = ASSETS / 'model-armor'
        self.assertTrue(folder.is_dir(), 'Model Armor assets are missing')
        for name, root_tag, source, fallback in [
            ('SUP-InspectPrompt', 'SanitizeUserPrompt', 'UserPromptSource', 'FunctionResponseSource'),
            ('SMR-InspectResponse', 'SanitizeModelResponse', 'LLMResponseSource', 'FunctionCallSource'),
        ]:
            policy = ET.parse(folder / (name + '.xml')).getroot()
            self.assertEqual(policy.tag, root_tag)
            self.assertEqual(policy.get('continueOnError'), 'false')
            self.assertEqual(policy.get('enabled'), 'true')
            self.assertEqual(policy.findtext('IgnoreUnresolvedVariables'), 'false')
            self.assertEqual(policy.findtext('UserPromptSource'), '{private.armor.prompt}')
            self.assertEqual(policy.findtext(source), policy.findtext(fallback))
            self.assertEqual(policy.findtext('ModelArmor/TemplateName'),
                             'projects/__TEMPLATE_PROJECT__/locations/__TEMPLATE_LOCATION__/templates/__TEMPLATE_ID__')
        for name, message, variable, jsonpath in [
            ('EV-ArmorPrompt', 'request', 'prompt', '$.messages[0].content'),
            ('EV-ArmorResponse', 'response', 'response', '$.choices[0].message.content'),
        ]:
            policy = ET.parse(folder / (name + '.xml')).getroot()
            self.assertEqual(policy.findtext('Source'), message)
            self.assertEqual(policy.findtext('VariablePrefix'), 'private.armor')
            extracted = policy.find('JSONPayload/Variable')
            assert extracted is not None
            self.assertEqual(extracted.get('name'), variable)
            self.assertEqual(policy.findtext('JSONPayload/Variable/JSONPath'), jsonpath)
            self.assertEqual(policy.findtext('IgnoreUnresolvedVariables'), 'false')

    def test_armor_flow_and_inline_parity(self):
        folder = ASSETS / 'model-armor'
        matches = examples_in('model-armor')
        self.assertEqual({p.name for p in folder.glob('*.xml')},
                         {Path(p).name for p, _ in matches})
        values = {'__TEMPLATE_PROJECT__': 'example-project', '__TEMPLATE_LOCATION__': 'us-central1',
                  '__TEMPLATE_ID__': 'example-template', '__INCOMPLETE_STATUS__': '503',
                  '__CALLER_AUTH_POLICY__': 'VAK-Test', '__REQUEST_VALIDATION_POLICY__': 'OAS-Test',
                  '__APPROVED_COUNT_CONDITION__': 'response.status.code = 200',
                  '__RESPONSE_VALIDATION_POLICY__': 'JS-TestResponse',
                  '__RESPONSE_PRIVACY_POLICY__': 'AM-TestPrivacy'}
        for path, snippet in matches:
            self.assertEqual(snippet.strip(), (ROOT / path).read_text().strip())
            for key, value in values.items():
                snippet = snippet.replace(key, value)  # fixed synthetic fixture only
            self.assertFalse(re.search(r'__[A-Z_]+__', snippet), path)
            ET.fromstring(snippet)
        flow = ET.parse(folder / 'proxy-flow-fragment.xml').getroot()
        self.assertEqual([x.text for x in flow.findall('Request/Step/Name')],
                         ['__CALLER_AUTH_POLICY__', '__REQUEST_VALIDATION_POLICY__', 'LTQ-Enforce',
                          'EV-ArmorPrompt', 'SUP-InspectPrompt', 'JS-ValidateArmorPrompt', 'RF-ArmorIncomplete'])
        self.assertEqual([x.text for x in flow.findall('Response/Step/Name')],
                         ['LTQ-Count', '__RESPONSE_VALIDATION_POLICY__', 'EV-ArmorResponse',
                          'SMR-InspectResponse', 'JS-ValidateArmorResponse', 'RF-ArmorIncomplete', '__RESPONSE_PRIVACY_POLICY__'])
        self.assertEqual(flow.findtext('Response/Step/Condition'), '__APPROVED_COUNT_CONDITION__')
        for phase in ['Request', 'Response']:
            key = 'prompt' if phase == 'Request' else 'response'
            guard = next(s for s in flow.findall(phase + '/Step') if s.findtext('Name') == 'RF-ArmorIncomplete')
            condition = guard.findtext('Condition')
            self.assertIn('private.armor.' + key + '_complete != true', condition)
            self.assertNotIn('requestSentToModelArmor', condition)
            policy = ET.parse(folder / ('JS-ValidateArmor' + key.title() + '.xml')).getroot()
            self.assertEqual(policy.findtext('Properties/Property'), key)
            self.assertEqual(policy.findtext('ResourceURL'), 'jsc://validate-armor.js')
        for step in flow.findall('Response/Step'):
            if step.findtext('Name') in ['EV-ArmorResponse', 'SMR-InspectResponse',
                                        'JS-ValidateArmorResponse', 'RF-ArmorIncomplete']:
                self.assertIn('response.status.code = 200', step.findtext('Condition'))
        fault = ET.parse(folder / 'RF-ArmorIncomplete.xml').getroot()
        self.assertEqual(fault.findtext('FaultResponse/Set/StatusCode'), '__INCOMPLETE_STATUS__')
        self.assertEqual(fault.findtext('FaultResponse/Set/Payload'), '{"error":"inspection_incomplete"}')

    def test_prompt_token_limit_native_contract(self):
        folder = ASSETS / 'prompt-token-limit'
        self.assertTrue(folder.is_dir(), 'PromptTokenLimit assets are missing')
        policy = ET.parse(folder / 'PTL-ProtectPromptBurst.xml').getroot()
        self.assertEqual(policy.tag, 'PromptTokenLimit')
        self.assertEqual(policy.attrib, {'name': 'PTL-ProtectPromptBurst',
                                        'continueOnError': 'false', 'enabled': 'true'})
        self.assertEqual([x.tag for x in policy], ['UserPromptSource', 'Identifier', 'Rate',
                                                  'UseEffectiveCount', 'IgnoreUnresolvedVariables'])
        self.assertEqual(policy.findtext('UserPromptSource'), '{private.ptl.prompt}')
        identifier, rate = policy.find('Identifier'), policy.find('Rate')
        assert identifier is not None and rate is not None
        self.assertEqual(identifier.attrib, {'ref': '__VERIFIED_CALLER_VARIABLE__'})
        self.assertEqual(policy.findtext('Rate'), '__PROMPT_TOKEN_RATE__')
        self.assertEqual(rate.attrib, {})
        self.assertEqual(policy.findtext('UseEffectiveCount'), 'true')
        self.assertEqual(policy.findtext('IgnoreUnresolvedVariables'), 'false')
        extraction = ET.parse(folder / 'EV-BurstPrompt.xml').getroot()
        self.assertEqual(extraction.findtext('Source'), 'request')
        self.assertEqual(extraction.findtext('VariablePrefix'), 'private.ptl')
        variable = extraction.find('JSONPayload/Variable')
        assert variable is not None
        self.assertEqual(variable.attrib,
                         {'name': 'prompt', 'type': 'string'})
        self.assertEqual(extraction.findtext('JSONPayload/Variable/JSONPath'), '__PROMPT_TEXT_JSONPATH__')
        self.assertEqual(extraction.findtext('IgnoreUnresolvedVariables'), 'false')

    def test_prompt_token_limit_flow_fault_and_inline_parity(self):
        folder = ASSETS / 'prompt-token-limit'
        matches = examples_in('prompt-token-limit')
        self.assertEqual({p.name for p in folder.glob('*.xml')},
                         {Path(p).name for p, _ in matches})
        values = {'__VERIFIED_CALLER_VARIABLE__': 'verifyapikey.VAK-Test.client_id',
                  '__PROMPT_TOKEN_RATE__': '100pm', '__PROMPT_TEXT_JSONPATH__': '$.messages[0].content',
                  '__CALLER_AUTH_POLICY__': 'VAK-Test', '__REQUEST_VALIDATION_POLICY__': 'JS-TestValidate'}
        for path, snippet in matches:
            self.assertEqual(snippet.strip(), (ROOT / path).read_text().strip(), path)
            for key, value in values.items():
                snippet = snippet.replace(key, value)  # fixed synthetic fixture only
            self.assertFalse(re.search(r'__[A-Z_]+__', snippet), path)
            ET.fromstring(snippet)
        flow = ET.parse(folder / 'proxy-flow-fragment.xml').getroot()
        self.assertEqual([x.text for x in flow.findall('Request/Step/Name')],
                         ['__CALLER_AUTH_POLICY__', '__REQUEST_VALIDATION_POLICY__',
                          'EV-BurstPrompt', 'PTL-ProtectPromptBurst'])
        self.assertEqual(flow.findall('Response/Step'), [])
        fault = ET.parse(folder / 'prompt-limit-fault-fragment.xml').getroot()
        self.assertEqual(fault.findtext('Condition'), '(fault.name = "PromptTokenLimitViolation")')
        self.assertNotIn('.failed', ET.tostring(fault, encoding='unicode'))
        name = fault.findtext('Step/Name')
        assert name is not None
        response = ET.parse(folder / (name + '.xml')).getroot()
        self.assertEqual(response.findtext('Set/StatusCode'), '429')
        self.assertEqual(response.findtext('Set/Payload'), '{"error":"prompt_token_rate_exceeded"}')
        self.assertIsNone(response.find('Set/Headers/Header[@name="Retry-After"]'))
        for step in flow.findall('Request/Step/Name'):
            assert step.text is not None
            if not step.text.startswith('__'):
                self.assertTrue((folder / (step.text + '.xml')).is_file())

    def test_prompt_token_limit_shared_and_rate_rendering(self):
        # Synthetic XML adaptations only, not evidence of runtime pooling or rate enforcement.
        source = (ASSETS / 'prompt-token-limit/PTL-ProtectPromptBurst.xml').read_text()
        for rate_value in ['100pm', '20ps']:
            for shared in [False, True]:
                with self.subTest(rate=rate_value, shared=shared):
                    policy = ET.fromstring(source)
                    rate, identifier = policy.find('Rate'), policy.find('Identifier')
                    assert rate is not None and identifier is not None
                    rate.text = rate_value
                    if shared:
                        policy.remove(identifier)
                    else:
                        identifier.set('ref', 'verifyapikey.VAK-Test.client_id')
                    rendered = ET.tostring(policy, encoding='unicode')
                    self.assertFalse(re.search(r'__[A-Z_]+__', rendered))
                    reparsed = ET.fromstring(rendered)
                    self.assertEqual(reparsed.findtext('UseEffectiveCount'), 'true')
                    self.assertEqual(reparsed.findtext('Rate'), rate_value)
                    self.assertEqual(reparsed.find('Identifier') is None, shared)

    def test_target_order(self):
        flow = ET.parse(ASSETS / 'target/target-request-flow.xml').getroot()
        self.assertEqual([x.text for x in flow.findall('Request/Step/Name')],
                         ['AM-PrepareTargetRequest', '__CREDENTIAL_LOOKUP_POLICY__', 'AM-SetUpstreamAuth'])
        policy = ET.parse(ASSETS / 'target/AM-PrepareTargetRequest.xml').getroot()
        self.assertEqual(policy.findtext('AssignVariable/Name'), 'target.copy.pathsuffix')
        self.assertEqual(policy.findtext('AssignVariable/Value'), 'false')

    def test_quota_render_and_pair(self):
        values = {'__COUNTER_NAME__': 'test-counter', '__VERIFY_API_KEY_POLICY__': 'VAK-Test',
                  '__VERIFIED_CALLER_VARIABLE__': 'verifyapikey.VAK-Test.client_id',
                  '__USAGE_JSONPATH__': '$.usage.total_tokens', '__SYNCHRONOUS__': 'true',
                  '__UPSTREAM_MODEL_VARIABLE__': 'ai.upstream_model'}
        policies = []
        for name in ['LTQ-Enforce', 'LTQ-Count']:
            text = (ASSETS / 'token-quota' / (name + '.xml')).read_text()
            for key, value in values.items():
                text = text.replace(key, value)  # fixed synthetic fixture, not a production renderer
            self.assertFalse(re.search(r'__[A-Z_]+__', text))
            policies.append(ET.fromstring(text))
        for field in ['SharedName', 'Allow', 'Interval', 'TimeUnit', 'Identifier', 'Distributed', 'Synchronous',
                      'IgnoreUnresolvedVariables', 'LLMModelSource']:
            left, right = policies[0].find(field), policies[1].find(field)
            assert left is not None and right is not None
            self.assertEqual(left.text, right.text)
            self.assertEqual(left.attrib, right.attrib)
        self.assertEqual(policies[0].findtext('EnforceOnly'), 'true')
        self.assertEqual(policies[1].findtext('CountOnly'), 'true')
        for policy, source in zip(policies, ['enforce', 'count']):
            with self.subTest(policy=source):
                allow = policy.find('Allow')
                assert allow is not None
                # Limit comes from the API Product; inline count is the fail-closed floor.
                self.assertTrue(allow.get('countRef', '').endswith('.apiproduct.developer.llmQuota.limit'))
                self.assertEqual(allow.get('count'), '1')
                for field, suffix in [('Interval', '.interval'), ('TimeUnit', '.timeunit')]:
                    element = policy.find(field)
                    assert element is not None
                    self.assertTrue(element.get('ref', '').endswith('.apiproduct.developer.llmQuota' + suffix))
        self.assertIn('$.usage.total_tokens', policies[1].findtext('LLMTokenUsageSource'))
        # Both halves key on the request-side backend model, never the response body.
        self.assertEqual(policies[0].findtext('LLMModelSource'), '{ai.upstream_model}')

    def test_quota_steps_and_user_choice(self):
        flow = ET.parse(ASSETS / 'token-quota/proxy-flow-fragment.xml').getroot()
        self.assertEqual(flow.findall('Request/Step/Name')[-1].text, 'LTQ-Enforce')
        self.assertEqual(flow.findtext('Response/Step/Name'), 'LTQ-Count')
        self.assertEqual(flow.findtext('Response/Step/Condition'), '__APPROVED_COUNT_CONDITION__')
        fault = ET.parse(ASSETS / 'token-quota/quota-fault-fragment.xml').getroot()
        name = fault.findtext('Step/Name')
        assert name is not None
        self.assertTrue((ASSETS / 'token-quota' / (name + '.xml')).is_file())

if __name__ == '__main__':
    unittest.main()
