import React from "react";

describe("index entry", () => {
  test("creates root and renders App", () => {
    const mockRender = jest.fn();
    const mockCreateRoot = jest.fn(() => ({ render: mockRender }));
    document.body.innerHTML = '<div id="root"></div>';

    jest.isolateModules(() => {
      jest.doMock("react-dom/client", () => ({
        __esModule: true,
        default: {
          createRoot: mockCreateRoot,
        },
        createRoot: mockCreateRoot,
      }));
      jest.doMock("./App", () => () => <div>App Root</div>);
      require("./index");
    });

    expect(mockCreateRoot).toHaveBeenCalledTimes(1);
    expect(mockRender).toHaveBeenCalledTimes(1);
  });
});
