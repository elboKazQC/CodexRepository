import MoxaAnalyzer from '../moxaAnalyzer';

/** Instantiate MoxaAnalyzer with a dummy API key and verify utility method. */
test('getUserFriendlyReport returns text', () => {
  process.env.OPENAI_API_KEY = 'dummy';
  const analyzer = new MoxaAnalyzer();
  const report = analyzer.getUserFriendlyReport({ score: 10, max_score: 100 });
  expect(typeof report).toBe('string');
});
