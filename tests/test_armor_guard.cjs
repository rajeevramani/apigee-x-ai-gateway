const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync(process.argv[2], 'utf8');
function clean() { return {sanitizationResult: {filterMatchState: 'NO_MATCH_FOUND', filterResults: {
  rai: {raiFilterResult: {executionState: 'EXECUTION_SUCCESS'}},
  sdp: {sdpFilterResult: {inspectResult: {executionState: 'EXECUTION_SUCCESS'}}},
  pi_and_jailbreak: {piAndJailbreakFilterResult: {executionState: 'EXECUTION_SUCCESS'}},
  malicious_uris: {maliciousUriFilterResult: {executionState: 'EXECUTION_SUCCESS'}}
}}}; }
let checks = 0;
for (const phase of ['prompt', 'response']) {
  const prefix = phase === 'prompt' ? 'SanitizeUserPrompt.SUP-InspectPrompt.' : 'SanitizeModelResponse.SMR-InspectResponse.';
  function run(result, invocation = 'SUCCESS', match = 'NO_MATCH_FOUND', boxed = true,
               required = 'rai,sdp,pi_and_jailbreak,malicious_uris') {
    let flag;
    const wrap = value => boxed && value != null ? new String(value) : value;
    const values = {};
    values[prefix + 'invocationResult'] = wrap(invocation);
    values[prefix + 'filterMatchState'] = wrap(match);
    values[prefix + 'responseFromModelArmor'] = wrap(typeof result === 'string' ? result : JSON.stringify(result));
    values[prefix + 'requestSentToModelArmor'] = '{"fixture":true}';
    vm.runInNewContext(source, {properties: {phase: wrap(phase), requiredFilters: wrap(required)}, context: {
      getVariable(name) { return values[name]; },
      setVariable(name, value) { assert.strictEqual(name, 'private.armor.' + phase + '_complete'); flag = value; }
    }});
    return flag;
  }
  function check(value, expected) { assert.strictEqual(value, expected); checks++; }
  check(run(clean()), true);
  check(run(clean(), 'SUCCESS', 'NO_MATCH_FOUND', false), true);
  for (const bad of [undefined, null, {}, '{bad', 'null', '[]']) check(run(bad), false);
  for (const bad of ['PARTIAL', 'FAILURE', '', null, undefined, 'true']) check(run(clean(), bad === undefined ? null : bad), false);
  check(run(clean(), 'SUCCESS', 'MATCH_FOUND'), false);
  let result = clean(); result.sanitizationResult.filterMatchState = 'MATCH_FOUND'; check(run(result), false);
  for (const filter of ['rai', 'sdp', 'pi_and_jailbreak', 'malicious_uris']) {
    result = clean(); delete result.sanitizationResult.filterResults[filter]; check(run(result), false);
    result = clean(); const entry = result.sanitizationResult.filterResults[filter];
    const state = filter === 'sdp' ? entry.sdpFilterResult.inspectResult : entry[Object.keys(entry)[0]];
    for (const value of ['EXECUTION_SKIPPED', 'EXECUTION_FAILED', null, true]) {
      state.executionState = value; check(run(result), false);
    }
  }
  // requiredFilters follows the template: a subset passes, extras and gaps fail closed.
  result = clean(); delete result.sanitizationResult.filterResults.sdp;
  check(run(result, 'SUCCESS', 'NO_MATCH_FOUND', true, 'rai, pi_and_jailbreak ,malicious_uris'), true);
  check(run(result), false);
  check(run(clean(), 'SUCCESS', 'NO_MATCH_FOUND', true, 'rai,csam'), false);
  result = clean(); result.sanitizationResult.filterResults.csam = {csamFilterFilterResult: {executionState: 'EXECUTION_SUCCESS'}};
  check(run(result, 'SUCCESS', 'NO_MATCH_FOUND', true, 'rai,csam'), true);
  result = clean(); result.sanitizationResult.filterResults.sdp = {sdpFilterResult: {deidentifyResult: {executionState: 'EXECUTION_SUCCESS'}}};
  check(run(result), true);
  for (const empty of ['', ' , ', null, '   ']) check(run(clean(), 'SUCCESS', 'NO_MATCH_FOUND', true, empty), false);
}
console.log(checks + ' Model Armor guard checks passed');
