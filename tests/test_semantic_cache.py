"""Semantic cache examples: offline structure/parity, never runtime simulation."""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from doc_checks import check_links, frontmatter, markdown_links, validate_metadata
from test_examples import examples_in

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'assets/examples/semantic-cache'


class SemanticCache(unittest.TestCase):
    def test_required_frontmatter_shape(self):
        metadata = frontmatter((ROOT / 'SKILL.md').read_text())
        validate_metadata(metadata)
        self.assertEqual(metadata['name'], 'apigee-x-ai-gateway')

    def test_discoverability_and_version(self):
        metadata = frontmatter((ROOT / 'SKILL.md').read_text())
        validate_metadata(metadata)
        readme = (ROOT / 'README.md').read_text()
        declared = re.findall(r'version\s+`([^`]+)`', readme, re.I)
        self.assertTrue(declared, 'README declared version missing')
        self.assertEqual(set(declared), {metadata['version']})
        for name in ['SKILL.md', 'README.md', 'references/capability-status.md']:
            self.assertIn('references/semantic-cache.md', check_links(ROOT, [ROOT / name]), name)
        # Navigation targets and declared version are contracts; heading wording is not.

    def test_setup_region_placeholder_and_sources(self):
        setup = (ROOT / 'references/semantic-cache-vertex-setup.md').read_text()
        self.assertLess(setup.index('__APPROVED_REGION__'), setup.index('```bash'))
        commands = '\n'.join(re.findall(r'```bash\n(.*?)\n```', setup, re.S))
        self.assertRegex(commands, r"export VERTEX_REGION=['\"]__APPROVED_REGION__['\"]")
        for url in [
            'https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations',
            'https://docs.cloud.google.com/vertex-ai/docs/general/locations',
        ]:
            self.assertIn(url, markdown_links(setup))
        # Review distinct availability, quotas/capacity/connectivity and helper scope.

    def test_setup_component_commands(self):
        setup = (ROOT / 'references/semantic-cache-vertex-setup.md').read_text()
        commands = '\n'.join(re.findall(r'```bash\n(.*?)\n```', setup, re.S))
        for command in ['gcloud ai indexes create', 'gcloud ai index-endpoints create',
                        'gcloud ai index-endpoints deploy-index']:
            self.assertIn(command, commands)
        self.assertIn('/publishers/google/models/{model}:predict', commands)
        # No custom-model/interactive-auth requirement and threshold calibration
        # semantics require review, not command or word presence.

    def test_native_policy_contract(self):
        self.assertTrue(FOLDER.is_dir(), 'Semantic cache assets are missing')
        lookup = ET.parse(FOLDER / 'SCL-LookupFAQ.xml').getroot()
        populate = ET.parse(FOLDER / 'SCP-PopulateFAQ.xml').getroot()
        for policy, tag in [(lookup, 'SemanticCacheLookup'), (populate, 'SemanticCachePopulate')]:
            self.assertEqual(policy.tag, tag)
            self.assertEqual(policy.get('continueOnError'), 'false')
            self.assertEqual(policy.findtext('IgnoreUnresolvedVariables'), 'false')
        self.assertEqual([x.tag for x in lookup],
                         ['IgnoreUnresolvedVariables', 'UserPromptSource', 'Embeddings', 'SimilaritySearch'])
        self.assertEqual(lookup.findtext('UserPromptSource'), '{private.semantic.prompt}')
        self.assertEqual(lookup.findtext('Embeddings/VertexAI/URL'), '__EMBEDDING_URL__')
        search = lookup.find('SimilaritySearch/VertexAI')
        assert search is not None
        self.assertEqual([x.tag for x in search],
                         ['URL', 'Threshold', 'DeployedIndexID', 'DistanceMeasureType'])
        self.assertEqual(search.findtext('Threshold'), '__THRESHOLD__')
        self.assertEqual(search.findtext('DeployedIndexID'), '__DEPLOYED_INDEX_ID__')
        self.assertEqual(search.findtext('DistanceMeasureType'), '__DISTANCE_MEASURE__')
        self.assertEqual([x.tag for x in populate],
                         ['IgnoreUnresolvedVariables', 'SimilaritySearch', 'TTLInSeconds'])
        populate_search = populate.find('SimilaritySearch/VertexAI')
        assert populate_search is not None
        self.assertEqual([x.tag for x in populate_search], ['URL'])
        self.assertEqual(populate.findtext('SimilaritySearch/VertexAI/URL'), '__UPSERT_URL__')
        self.assertEqual(populate.findtext('TTLInSeconds'), '__TTL_SECONDS__')

    def test_trial_checklist_coverage_and_point_of_use_links(self):
        workflow = (ROOT / 'references/semantic-cache.md').read_text()
        anchor = '#cache-trial-and-enablement-checklist'
        checklist = workflow.split('### Cache trial and enablement checklist\n', 1)[1]
        rows = [line.strip('|').split('|') for line in checklist.splitlines()
                if line.startswith('|')][2:]
        expected = {'PREP', 'BOUNDS', 'HIT', 'QUALITY', 'TTL', 'SAFETY',
                    'ELIGIBILITY', 'ACCOUNTING', 'OUTAGE', 'RETENTION'}
        ids = [row[0].strip() for row in rows]
        self.assertEqual(set(ids), expected)
        self.assertEqual(len(ids), len(expected), 'Duplicate checklist IDs')
        for row in rows:
            self.assertEqual(len(row), 3)
            self.assertTrue(all(cell.strip() for cell in row))
        sections = [
            ('## Scope and evidence boundary', '## Decisions before rendering or setup'),
            ('### Preserve existing flow behavior', '## Manual pre-import handoff'),
            ('## Manual pre-import handoff', '## Retention, rollback and cost'),
        ]
        for start, end in sections:
            section = workflow.split(start, 1)[1].split(end, 1)[0]
            # Slices still need the document's reference definitions.
            definitions = '\n'.join(re.findall(r'^\[[^\]]+\]: .+$', workflow, re.M))
            self.assertIn(anchor, markdown_links(section + '\n' + definitions), start)
        setup = (ROOT / 'references/semantic-cache-vertex-setup.md').read_text()
        for section in [setup.split('## 1.', 1)[0],
                        setup.split('## 5.', 1)[1].split('## 6.', 1)[0]]:
            self.assertIn('semantic-cache.md' + anchor, markdown_links(section))
        for owner in ['README.md', 'SKILL.md']:
            self.assertIn('references/semantic-cache.md' + anchor,
                          markdown_links((ROOT / owner).read_text()))
        for target in ['#decisions-before-rendering-or-setup',
                       '#manual-pre-import-handoff', '#retention-rollback-and-cost']:
            self.assertIn(target, markdown_links(checklist))
        # Rows and links do not prove approvals, safety,
        # fresh-only accounting, deletion, cost/residency or runtime behavior.


    def test_inline_parity_rendering_and_transport(self):
        matches = examples_in('semantic-cache')
        self.assertEqual({p.name for p in FOLDER.glob('*.xml')},
                         {Path(p).name for p, _ in matches})
        values = {
            '__EMBEDDING_URL__': 'https://us-central1-aiplatform.googleapis.com/v1/projects/test-project/locations/us-central1/publishers/google/models/gemini-embedding-001:predict',
            '__FIND_NEIGHBORS_URL__': 'https://test.vdb.vertexai.goog/v1/projects/test-project/locations/us-central1/indexEndpoints/123:findNeighbors',
            '__UPSERT_URL__': 'https://us-central1-aiplatform.googleapis.com/v1/projects/test-project/locations/us-central1/indexes/456:upsertDatapoints',
            '__DEPLOYED_INDEX_ID__': 'faq_test', '__THRESHOLD__': '0.95',
            '__DISTANCE_MEASURE__': 'DOT_PRODUCT_DISTANCE', '__TTL_SECONDS__': '60',
            '__PSC_TARGET_HOST__': '10.0.0.1',
            '__CALLER_AUTH_POLICY__': 'VAK-Test', '__REQUEST_VALIDATION_POLICY__': 'JS-Validate',
            '__CACHE_ELIGIBILITY_AND_PROMPT_POLICY__': 'JS-Eligibility',
            '__EXISTING_QUOTA_AND_BURST_STEPS__': 'FC-Admission',
            '__PROMPT_ARMOR_AND_COMPLETENESS_STEPS__': 'FC-PromptProtection',
            '__RESPONSE_ARMOR_VALIDATION_AND_PRIVACY_STEPS__': 'FC-ResponseProtection',
            '__APPROVED_FRESH_COUNT_CONDITION__': 'test.fresh = true',
            '__APPROVED_SAFE_POPULATE_CONDITION__': 'test.safe = true',
        }
        rendered = {}
        for path, snippet in matches:
            self.assertEqual(snippet.strip(), (ROOT / path).read_text().strip(), path)
            for key, value in values.items():
                snippet = snippet.replace(key, value)  # synthetic offline fixture only
            self.assertFalse(re.search(r'__[A-Z_]+__', snippet), path)
            rendered[Path(path).name] = ET.fromstring(snippet)
        lookup = rendered['SCL-LookupFAQ.xml']
        old_search = lookup.find('SimilaritySearch')
        assert old_search is not None
        lookup.remove(old_search)
        lookup.append(rendered['psc-search-fragment.xml'])
        search = lookup.find('SimilaritySearch/VertexAI')
        assert search is not None
        self.assertIsNone(search.find('URL'))
        self.assertEqual(search.findtext('PrivateServiceConnect/GrpcEndpoint'), 'grpc://10.0.0.1:10000')
        self.assertIsNone(rendered['SCP-PopulateFAQ.xml'].find('.//PrivateServiceConnect'))

    def test_flow_gates_preserve_protection(self):
        self.assertTrue((FOLDER / 'proxy-flow-fragment.xml').is_file(), 'Flow guide is missing')
        flow = ET.parse(FOLDER / 'proxy-flow-fragment.xml').getroot()
        self.assertEqual([s.findtext('Name') for s in flow.findall('Request/Step')], [
            '__CALLER_AUTH_POLICY__', '__REQUEST_VALIDATION_POLICY__',
            '__CACHE_ELIGIBILITY_AND_PROMPT_POLICY__', '__EXISTING_QUOTA_AND_BURST_STEPS__',
            '__PROMPT_ARMOR_AND_COMPLETENESS_STEPS__', 'SCL-LookupFAQ'])
        self.assertEqual([s.findtext('Name') for s in flow.findall('Response/Step')], [
            'LTQ-Count', '__RESPONSE_ARMOR_VALIDATION_AND_PRIVACY_STEPS__', 'SCP-PopulateFAQ'])
        lookup = flow.findall('Request/Step')[-1].findtext('Condition')
        populate = flow.findall('Response/Step')[-1].findtext('Condition')
        count = flow.findtext('Response/Step/Condition')
        for condition in [lookup, populate]:
            assert condition is not None
            self.assertIn('(private.semantic.enabled = true)', condition)
            self.assertIn('(private.semantic.eligible = true)', condition)
        assert populate is not None and count is not None
        self.assertIn('SemanticCacheLookup.SCL-LookupFAQ.cache_hit = false', populate)
        self.assertIn('__APPROVED_SAFE_POPULATE_CONDITION__', populate)
        self.assertIn('!(SemanticCacheLookup.SCL-LookupFAQ.cache_hit = true)', count)
        self.assertIn('__APPROVED_FRESH_COUNT_CONDITION__', count)
        self.assertEqual(flow.findall('.//RouteRule'), [])
        self.assertEqual(flow.findall('.//AssignMessage'), [])


if __name__ == '__main__':
    unittest.main()
