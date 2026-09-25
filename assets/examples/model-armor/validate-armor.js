// Validate the Model Armor response JSON; fail closed by default.
// requiredFilters lists the filters enabled in the approved template, comma-separated.
var phase = String(properties.phase);
var prefix = phase === 'prompt' ? 'SanitizeUserPrompt.SUP-InspectPrompt.' : 'SanitizeModelResponse.SMR-InspectResponse.';
var flag = 'private.armor.' + phase + '_complete';
context.setVariable(flag, false);

function executionState(entry) {
  // Each filter result holds one inner object, e.g. {raiFilterResult: {...}}.
  var keys = Object.keys(entry);
  if (keys.length !== 1) return null;
  var inner = entry[keys[0]];
  if (inner.inspectResult) inner = inner.inspectResult;  // basic SDP
  else if (inner.deidentifyResult) inner = inner.deidentifyResult;  // advanced SDP
  return inner.executionState;
}

try {
  var required = String(properties.requiredFilters).split(',');
  var names = [];
  for (var r = 0; r < required.length; r++) {
    var name = required[r].replace(/^\s+|\s+$/g, '');
    if (name) names.push(name);
  }
  if (names.length > 0 &&
      String(context.getVariable(prefix + 'invocationResult')) === 'SUCCESS' &&
      String(context.getVariable(prefix + 'filterMatchState')) === 'NO_MATCH_FOUND') {
    var raw = context.getVariable(prefix + 'responseFromModelArmor');
    var result = JSON.parse(String(raw)).sanitizationResult;
    var filters = result.filterResults;
    var complete = result.filterMatchState === 'NO_MATCH_FOUND';
    for (var i = 0; i < names.length; i++) {
      complete = complete && executionState(filters[names[i]]) === 'EXECUTION_SUCCESS';
    }
    context.setVariable(flag, complete);
  }
} catch (ignored) {
  // Absent, malformed or incomplete results remain rejected; never log content.
}
