import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { useService } from "@web/core/utils/hooks";

const OPEN_STAGES = ["draft", "confirmed", "in_progress"];

export class LibreFleetDashboard extends Component {
    static template = "librefleet.Dashboard";
    // A client action receives the action record itself as a prop, plus a few
    // the action service adds. Spread these or OWL rejects the render.
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ technicians: [], openCount: 0, loading: true });
        onWillStart(async () => {
            await this.load();
        });
    }

    async load() {
        const domain = [["stage", "in", OPEN_STAGES]];
        // One round trip that groups and aggregates in Postgres, instead of
        // fetching every order and counting in JavaScript. On a real fleet
        // that difference is the whole chapter.
        const groups = await this.orm.formattedReadGroup(
            "librefleet.service.order",
            domain,
            ["technician_ids"],
            ["__count", "margin:sum"]
        );
        this.state.technicians = groups.map((group) => ({
            // Grouping by a many2many yields [id, name] per group, or false
            // for the records that have nobody assigned.
            id: group.technician_ids ? group.technician_ids[0] : false,
            name: group.technician_ids ? group.technician_ids[1] : "Unassigned",
            count: group.__count,
            margin: group["margin:sum"] || 0,
            domain: group.__domain,
        }));
        this.state.openCount = await this.orm.searchCount(
            "librefleet.service.order", domain);
        this.state.loading = false;
    }

    // Every group carries the domain that produced it, so "show me these
    // records" needs no domain rebuilt by hand and cannot drift from the
    // number the reader just clicked.
    openGroup(technician) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `Open orders: ${technician.name}`,
            res_model: "librefleet.service.order",
            domain: technician.domain,
            views: [[false, "list"], [false, "form"]],
        });
    }
}

registry.category("actions").add("librefleet_dashboard", LibreFleetDashboard);
