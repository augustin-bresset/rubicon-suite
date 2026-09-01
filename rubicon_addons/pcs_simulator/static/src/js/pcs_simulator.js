/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillUnmount } from "@odoo/owl";

const MODEL = "pcs.simulator";

// Schematic layout of the factory, one lane per production phase
// (mirrors the flow diagram of the company audit).
const NODE_W = 104;
const NODE_H = 44;
const X0 = 96;
const GAP_X = 136;
const Y0 = 24;
const GAP_Y = 92;

// Muted, matte palette: ochre / slate / plum / sage, brick for repairs.
const LANES = [
    { label: "Stone", color: "#a8763e",
      codes: ["AST", "SHP", "CUT", "SRD", "SFN"] },
    { label: "Metal", color: "#52708f",
      codes: ["WAX", "CST", "QC1", "FIL", "QC2", "PPL", "QC3"] },
    { label: "Assembly", color: "#7a6684",
      codes: ["ASM", "QC4", "MER", "SET", "QC5", "POL", "QC6"] },
    { label: "Finishing", color: "#5e7d6d",
      codes: ["ENG", "QC7", "PLT", "QC8", "FIN"] },
];
// Repair departments sit beside the flow and are reached on QC failures.
const SIDE_NODES = [
    { code: "QC11", lane: 1, color: "#96524b" },
    { code: "RST", lane: 2, color: "#96524b" },
];

export class PcsSimulator extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            status: { sim_time: "", tick_count: 0, seed: 42,
                      documents: [], events: [] },
            flow: { sim_time: "", total_pieces: 0, done: 0,
                    nodes: {}, transfers: [] },
            ordersCount: "3",
            historyDays: "30",
            customHours: "12",
            busy: false,
            playing: false,
            showEvents: false,

            // Virtual scanner: the simulated pieces with their barcodes
            showPieces: false,
            pieces: [],
            scanConfig: { departments: [], employees: [] },
            scanDeptId: "",
            scanEmployeeId: "",
        });

        this.layout = this.buildLayout();
        this.chainEdges = this.buildChainEdges();
        this.playTimer = null;

        onWillStart(async () => {
            await this.refresh();
        });
        onWillUnmount(() => {
            this.stopPlaying();
        });
    }

    // ── Schematic geometry ──────────────────────────────────────────────

    buildLayout() {
        const layout = {};
        LANES.forEach((lane, laneIndex) => {
            lane.codes.forEach((code, i) => {
                layout[code] = {
                    code,
                    x: X0 + i * GAP_X,
                    y: Y0 + laneIndex * GAP_Y,
                    color: lane.color,
                };
            });
        });
        for (const side of SIDE_NODES) {
            layout[side.code] = {
                code: side.code,
                x: X0 + 7 * GAP_X,
                y: Y0 + side.lane * GAP_Y,
                color: side.color,
            };
        }
        return layout;
    }

    center(node) {
        return { cx: node.x + NODE_W / 2, cy: node.y + NODE_H / 2 };
    }

    edgePath(fromCode, toCode) {
        const a = this.layout[fromCode];
        const b = this.layout[toCode];
        if (!a || !b) {
            return "";
        }
        if (a.y === b.y) {
            const y = a.y + NODE_H / 2;
            return `M ${a.x + NODE_W} ${y} L ${b.x} ${y}`;
        }
        const ax = a.x + NODE_W / 2;
        const bx = b.x + NODE_W / 2;
        const ay = a.y + (b.y > a.y ? NODE_H : 0);
        const by = b.y + (b.y > a.y ? 0 : NODE_H);
        const bend = b.y > a.y ? 36 : -36;
        return `M ${ax} ${ay} C ${ax} ${ay + bend}, ${bx} ${by - bend}, ${bx} ${by}`;
    }

    entryPath(toCode) {
        const b = this.layout[toCode];
        const y = b.y + NODE_H / 2;
        return `M ${b.x - 44} ${y} L ${b.x} ${y}`;
    }

    buildChainEdges() {
        const edges = [];
        for (const lane of LANES) {
            for (let i = 0; i < lane.codes.length - 1; i++) {
                edges.push({ d: this.edgePath(lane.codes[i], lane.codes[i + 1]),
                             dashed: false });
            }
        }
        // Lane-to-lane continuation of the metal chain, and the stone
        // track joining the assembly at Merged.
        edges.push({ d: this.edgePath("QC3", "ASM"), dashed: false });
        edges.push({ d: this.edgePath("QC6", "ENG"), dashed: false });
        edges.push({ d: this.edgePath("SFN", "MER"), dashed: true });
        return edges;
    }

    get flowNodes() {
        return Object.values(this.layout).map((node) => {
            const counts = this.state.flow.nodes[node.code] || {};
            return {
                ...node,
                ...this.center(node),
                name: counts.name || node.code,
                isQc: counts.is_qc || false,
                color: counts.is_qc ? "#7d7d7d" : node.color,
                wip: counts.wip || 0,
                fin: counts.fin || 0,
            };
        });
    }

    get flowTransfers() {
        return this.state.flow.transfers
            .filter((t) => this.layout[t.to])
            .map((t, index) => {
                const d = t.origin && this.layout[t.origin]
                    ? this.edgePath(t.origin, t.to)
                    : this.entryPath(t.to);
                const target = this.layout[t.to];
                return { id: index, d, count: t.count,
                         lx: target.x - 10, ly: target.y + NODE_H / 2 - 8 };
            });
    }

    get laneLabels() {
        return LANES.map((lane, i) => ({
            label: lane.label, color: lane.color,
            x: 8, y: Y0 + i * GAP_Y + NODE_H / 2,
        }));
    }

    // ── RPC plumbing ────────────────────────────────────────────────────

    async refresh() {
        const [status, flow] = await Promise.all([
            this.orm.call(MODEL, "get_status", []),
            this.orm.call(MODEL, "get_flow", []),
        ]);
        this.state.status = status;
        this.state.flow = flow;
    }

    async run(method, args, doneMessage) {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        try {
            await this.orm.call(MODEL, method, args);
            await this.refresh();
            if (doneMessage) {
                this.notification.add(doneMessage, { type: "success" });
            }
        } catch (error) {
            this.stopPlaying();
            this.notification.add(
                error.data?.message || String(error), { type: "danger" });
        } finally {
            this.state.busy = false;
        }
    }

    setupSim() {
        return this.run("setup", [parseInt(this.state.ordersCount) || 3],
                        "Simulation ready.");
    }

    advance(hours) {
        return this.run("advance_hours", [hours]);
    }

    advanceCustom() {
        const hours = parseFloat(this.state.customHours);
        if (hours > 0) {
            this.advance(hours);
        }
    }

    async stepOperation() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        try {
            const status = await this.orm.call(MODEL, "step_operation", []);
            await this.refresh();
            if (!status.event) {
                this.notification.add(
                    "Nothing happens anymore: every piece is finished.",
                    { type: "warning" });
            } else {
                const lines = status.event_lines || [];
                const shown = lines.slice(0, 4).join(" — ");
                const more = lines.length > 4
                    ? ` (+${lines.length - 4} more)` : "";
                this.notification.add(
                    `After ${status.elapsed_hours}h: ${shown}${more}`,
                    { type: "info" });
            }
        } catch (error) {
            this.notification.add(
                error.data?.message || String(error), { type: "danger" });
        } finally {
            this.state.busy = false;
        }
    }

    async toggleAttached(ev) {
        await this.orm.call(MODEL, "set_attached", [ev.target.checked]);
        await this.refresh();
    }

    runHistory() {
        const days = parseInt(this.state.historyDays) || 30;
        return this.run("run_history", [days],
                        `${days} days of history generated.`);
    }

    resetSim() {
        this.stopPlaying();
        return this.run("reset", [], "Simulation data removed.");
    }

    // ── Virtual scanner ─────────────────────────────────────────────────

    async togglePieces() {
        if (!this.state.showPieces && !this.state.scanConfig.departments.length) {
            this.state.scanConfig = await this.orm.call(
                "pcs.workspace.service", "get_scan_config", []);
        }
        if (!this.state.showPieces) {
            await this.loadPieces();
        }
        this.state.showPieces = !this.state.showPieces;
    }

    async loadPieces() {
        this.state.pieces = await this.orm.call("pcs.simulator", "get_pieces", []);
    }

    get scanWorkers() {
        const deptId = parseInt(this.state.scanDeptId);
        if (!deptId) {
            return this.state.scanConfig.employees;
        }
        return this.state.scanConfig.employees.filter(
            (e) => !e.department_ids.length || e.department_ids.includes(deptId));
    }

    async scanPiece(piece) {
        if (!this.state.scanDeptId) {
            this.notification.add("Select a department to scan into.",
                                  { type: "warning" });
            return;
        }
        const result = await this.orm.call("pcs.simulator", "scan_piece", [
            piece.barcode,
            parseInt(this.state.scanDeptId),
            this.state.scanEmployeeId ? parseInt(this.state.scanEmployeeId) : false,
            0,
        ]);
        const type = { issued: "success", received: "info" }[result.status] || "danger";
        this.notification.add(result.message, { type });
        await Promise.all([this.refresh(), this.loadPieces()]);
    }

    async printCard(piece) {
        const reportAction = await this.orm.call(
            "pcs.barcode", "action_print_stock_cards", [[piece.id]]);
        await this.action.doAction(reportAction);
    }

    // ── Play mode: one 8h tick every 1.5s ───────────────────────────────

    togglePlay() {
        if (this.state.playing) {
            this.stopPlaying();
            return;
        }
        this.state.playing = true;
        this.playTimer = setInterval(() => this.advance(8), 1500);
    }

    stopPlaying() {
        if (this.playTimer) {
            clearInterval(this.playTimer);
            this.playTimer = null;
        }
        this.state.playing = false;
    }

    async changeSeed(ev) {
        const seed = parseInt(ev.target.value) || 42;
        await this.orm.call(MODEL, "set_seed", [seed]);
        await this.refresh();
    }
}

PcsSimulator.template = "pcs_simulator.PcsSimulator";
registry.category("actions").add("pcs_simulator_action", PcsSimulator);
