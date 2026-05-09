jest.mock("axios", () => ({
  defaults: {},
}));

describe("api config", () => {
  const originalBackend = process.env.REACT_APP_BACKEND_URL;

  afterEach(() => {
    jest.resetModules();
    if (originalBackend === undefined) {
      delete process.env.REACT_APP_BACKEND_URL;
    } else {
      process.env.REACT_APP_BACKEND_URL = originalBackend;
    }
  });

  it("builds API URL from REACT_APP_BACKEND_URL and trims trailing slash", () => {
    process.env.REACT_APP_BACKEND_URL = "https://backend.example.com/";

    jest.isolateModules(() => {
      const { API_BASE, API } = require("./api");
      const axios = require("axios");

      expect(API_BASE).toBe("https://backend.example.com");
      expect(API).toBe("https://backend.example.com/api");
      expect(axios.defaults.withCredentials).toBe(true);
      expect(axios.defaults.timeout).toBe(15000);
    });
  });

  it("falls back safely when backend URL env is missing", () => {
    delete process.env.REACT_APP_BACKEND_URL;
    const warnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});

    jest.isolateModules(() => {
      const { API_BASE, API } = require("./api");

      expect(API_BASE.length).toBeGreaterThan(0);
      expect(API).toBe(`${API_BASE}/api`);
    });

    expect(warnSpy).toHaveBeenCalled();
    warnSpy.mockRestore();
  });
});
