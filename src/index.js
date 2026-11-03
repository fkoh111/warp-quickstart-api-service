'use strict';

function greet(name) {
  if (typeof name !== 'string' || name.trim() === '') {
    throw new TypeError('name must be a non-empty string');
  }
  return `Hello, ${name.trim()}!`;
}

function sum(a, b) {
  if (typeof a !== 'number' || typeof b !== 'number') {
    throw new TypeError('a and b must be numbers');
  }
  return a + b;
}

module.exports = { greet, sum };
