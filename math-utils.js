/**
 * Performs basic addition of two numbers
 * @param {number} a - The first number
 * @param {number} b - The second number
 * @returns {number} The sum of a and b
 */
function add(a, b) {
  return a + b;
}

/**
 * Adds multiple numbers together
 * @param {...number} numbers - Variable number of arguments to add
 * @returns {number} The sum of all numbers
 */
function addMultiple(...numbers) {
  return numbers.reduce((sum, num) => sum + num, 0);
}

// Export for use in other modules
module.exports = { add, addMultiple };

// Example usage
if (require.main === module) {
  console.log('5 + 3 =', add(5, 3));           // 8
  console.log('10 + 20 =', add(10, 20));       // 30
  console.log('1 + 2 + 3 + 4 =', addMultiple(1, 2, 3, 4)); // 10
}
