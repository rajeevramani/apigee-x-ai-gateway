// Works out the cost of one model response in micro-US-dollars (1 USD = 1,000,000).
// Prices come from API product custom attributes, in USD per 1 million tokens.
// USD per 1 million tokens is numerically the same as micro-USD per token.
// Sets cost.microusd (whole number, rounded up) and cost.valid ("true"/"false").
// ECMAScript 5.1 only: no let/const, arrow functions or template literals.

function isTokenCount(n) {
  return typeof n === 'number' && isFinite(n) && n >= 0 && Math.floor(n) === n;
}

function readPrice(name) {
  var raw = context.getVariable(name);
  if (raw === null || raw === undefined || String(raw).replace(/\s/g, '') === '') {
    return null;
  }
  var price = Number(raw);
  return (isFinite(price) && price >= 0) ? price : null;
}

var valid = false;
var cost = 0;

try {
  var alias = context.getVariable(properties.modelAliasVariable);
  var prefix = 'verifyapikey.' + properties.verifyApiKeyPolicy + '.apiproduct.';
  var priceIn = alias ? readPrice(prefix + 'price_input_per_1m_' + alias) : null;
  var priceOut = alias ? readPrice(prefix + 'price_output_per_1m_' + alias) : null;
  var body = JSON.parse(context.getVariable('response.content'));
  var usage = body && body.usage;
  var promptTokens = usage ? usage.prompt_tokens : null;
  var completionTokens = usage ? usage.completion_tokens : null;

  if (priceIn !== null && priceOut !== null &&
      isTokenCount(promptTokens) && isTokenCount(completionTokens)) {
    var raw = promptTokens * priceIn + completionTokens * priceOut;
    // Trim floating-point noise (e.g. 7.000000000000001) before rounding up.
    cost = Math.ceil(Math.round(raw * 1000000) / 1000000);
    valid = true;
  }
} catch (e) {
  valid = false;
}

context.setVariable('cost.microusd', String(cost));
context.setVariable('cost.valid', String(valid));
