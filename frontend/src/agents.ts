// Turn the backend's event stream into "what each agent is doing" and a per-agent summary.
import type { AgentEvent, Role } from "./types";
import { ROLES } from "./types";

export const ROLE_COLOR: Record<string, string> = {
  boss: "#253a55",             // deep warm navy
  inventory: "#5d7a6c",        // grey-sage
  accounting: "#4f6f92",       // warm slate blue
  facilities: "#77708a",       // heather grey-violet
  customer_service: "#4a7d8a", // dusty teal-blue
  system: "#878a90",
  human: "#9a4a45",
};

/** Aviation crew titles shown under each agent's name. */
export const CREW: Record<string, string> = {
  boss: "Captain",
  inventory: "Cargo master",
  accounting: "Purser",
  facilities: "Ground crew",
  customer_service: "Cabin crew",
};

export interface AgentView {
  role: Role;
  state: "idle" | "working" | "done";
  says: string;              // the latest thing it said, or what it is doing now
  tools: Map<string, number>; // MCP tools it called, with counts
  lastTool?: string;
  handoffsIn: { from: string; request: string }[];
  handoffsOut: { to: string; request: string }[];
  finalSummary: string;
  steps: number;
}

export function shortArgs(args?: Record<string, unknown>): string {
  if (!args) return "";
  const vals = Object.values(args).map((v) => (typeof v === "string" ? v : JSON.stringify(v)));
  return vals.join(", ");
}

export function agentViews(events: AgentEvent[], running: boolean): AgentView[] {
  const views = new Map<string, AgentView>();
  for (const r of ROLES) {
    views.set(r, { role: r, state: "idle", says: "", tools: new Map(), handoffsIn: [], handoffsOut: [], finalSummary: "", steps: 0 });
  }
  const lastWasFinal = new Map<string, boolean>();
  for (const e of events) {
    if (e.kind === "handoff" && e.to_role && views.has(e.to_role)) {
      const to = views.get(e.to_role)!;
      to.handoffsIn.push({ from: e.role, request: e.text ?? "" });
      to.state = "working";
      to.says = `Picked up a request from ${label(e.role)}…`;
      lastWasFinal.set(e.to_role, false);
    }
    const v = views.get(e.role);
    if (!v) continue;
    v.steps += 1;
    if (e.kind === "tool_call" && e.tool) {
      v.tools.set(e.tool, (v.tools.get(e.tool) ?? 0) + 1);
      v.lastTool = `${e.tool}(${shortArgs(e.args)})`;
      v.says = `Checking ${v.lastTool}`;
      v.state = "working";
      lastWasFinal.set(e.role, false);
    } else if (e.kind === "handoff" && e.to_role) {
      v.handoffsOut.push({ to: e.to_role, request: e.text ?? "" });
      v.says = `Asked ${label(e.to_role)}: ${e.text ?? ""}`;
      v.state = "working";
      lastWasFinal.set(e.role, false);
    } else if (e.kind === "said" && e.text) {
      v.says = e.text.replace(/^Asked: /, "Took the ticket: ");
      if (e.final) {
        v.finalSummary = e.text;
        lastWasFinal.set(e.role, true);
      } else {
        v.state = "working";
        lastWasFinal.set(e.role, false);
      }
    }
  }
  for (const v of views.values()) {
    if (v.steps === 0 && v.handoffsIn.length === 0) v.state = "idle";
    else if (lastWasFinal.get(v.role) || !running) v.state = "done";
    else v.state = "working";
  }
  return ROLES.map((r) => views.get(r)!);
}

export function label(role: string): string {
  return ({
    boss: "The Boss", inventory: "Inventory", accounting: "Accounting", facilities: "Facilities",
    customer_service: "Customer Service", system: "Desk", human: "You",
  } as Record<string, string>)[role] ?? role;
}

/** One readable line per event for the live timeline. */
export function describe(e: AgentEvent): { verb: string; rest: string } | null {
  switch (e.kind) {
    case "run_started": return { verb: "Opened", rest: e.text ?? "" };
    case "tool_call": return { verb: "Used", rest: `${e.tool}(${shortArgs(e.args)})` };
    case "tool_result": return null; // noisy; the agent's own words cover it
    case "handoff": return { verb: `Asked ${label(e.to_role ?? "")}`, rest: e.text ?? "" };
    case "said": return { verb: e.final ? "Reported" : "Said", rest: (e.text ?? "").replace(/^Asked: /, "") };
    case "decision": return { verb: "Final call", rest: `${e.text ?? ""}${e.status ? ` · ${e.status.replace("_", " ")}` : ""}` };
    case "resolved": return { verb: "Resolved", rest: e.text ?? "" };
    case "approval": return { verb: e.status === "paid" ? "Approved" : e.status === "rejected" ? "Rejected" : "Approval refused", rest: e.text ?? "" };
    case "warning": return { verb: "Note", rest: e.text ?? "" };
    case "reset": return { verb: "Reset", rest: e.text ?? "" };
    default: return null;
  }
}
