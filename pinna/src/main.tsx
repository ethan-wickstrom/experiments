import { render } from "preact";
import { App } from "./app/App.tsx";
import "./app/style.css";

render(<App />, document.getElementById("app")!);
