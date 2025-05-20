export const window = {
  showInformationMessage: jest.fn(),
  showErrorMessage: jest.fn(),
  showWarningMessage: jest.fn(),
  withProgress: jest.fn((opts, task) => task({ report: () => {} })),
};
export const workspace = {
  getConfiguration: jest.fn(() => ({ get: jest.fn() })),
  fs: { writeFile: jest.fn(), readFile: jest.fn() },
};
export const ProgressLocation = { Notification: 0 };
export const Uri = { file: jest.fn() } as any;
export const commands = { executeCommand: jest.fn() };
