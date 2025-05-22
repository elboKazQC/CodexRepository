import { LogsViewProvider } from '../logsViewProvider';

/** Simple test to ensure the provider can be instantiated. */
test('creates LogsViewProvider without crashing', () => {
  const provider = new LogsViewProvider({} as any);
  expect(provider).toBeInstanceOf(LogsViewProvider);
});
