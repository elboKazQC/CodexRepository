import { ConfigurationViewProvider } from '../configurationViewProvider';

/** Ensure default configuration contains expected keys. */
test('returns default configuration', () => {
  const provider = new ConfigurationViewProvider({} as any);
  const cfg = provider.getCurrentConfig();
  expect(cfg).toHaveProperty('min_transmission_rate');
  expect(cfg).toHaveProperty('max_transmission_power');
});
