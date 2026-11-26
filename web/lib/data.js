import { spawn } from "node:child_process";
import path from "node:path";
import { hostedData } from "./hosted";

export function data(operation, params = {}) {
  if (process.env.VERCEL || process.env.NORTHGATE_EVIDENCE_URL) {
    return hostedData(operation, params);
  }
  return new Promise((resolve, reject) => {
    const dir = path.resolve(process.cwd(), "..");
    const child = spawn(
      /* turbopackIgnore: true */ process.env.NORTHGATE_PYTHON || "python",
      ["-B", "web_service.py"],
      {
        cwd: dir,
        windowsHide: true,
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      },
    );
    let output = "";
    const timer = setTimeout(() => child.kill(), 90000);
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      output += chunk;
    });
    child.stderr.resume();
    child.stdin.on("error", () => {});
    child.on("error", () => {
      clearTimeout(timer);
      reject(new Error("Python could not start. Check the installation."));
    });
    child.on("close", () => {
      clearTimeout(timer);
      try {
        const response = JSON.parse(output);
        if (response.error) throw new Error(response.error);
        resolve(response.data);
      } catch (error) {
        reject(
          error instanceof SyntaxError
            ? new Error("Evidence service unavailable.")
            : error,
        );
      }
    });
    child.stdin.end(JSON.stringify({ op: operation, args: params }));
  });
}
