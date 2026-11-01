// The basic Plotly bundle (scatter, bar, pie) ships without typings; it exposes the plotly.js API.
declare module "plotly.js-basic-dist-min" {
  import * as Plotly from "plotly.js";
  export = Plotly;
}
