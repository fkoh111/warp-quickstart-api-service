'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { greet, sum } = require('../src/index.js');

test('greet returns a greeting', () => {
  assert.equal(greet('Warp'), 'Hello, Warp!');
});

test('greet trims whitespace', () => {
  assert.equal(greet('  Warp  '), 'Hello, Warp!');
});

test('sum adds numbers', () => {
  assert.equal(sum(2, 3), 5);
});
