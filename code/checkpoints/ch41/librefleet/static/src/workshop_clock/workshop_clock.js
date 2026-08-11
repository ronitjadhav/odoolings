import { Component, onWillStart, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class WorkshopClock extends Component {
    static template = "librefleet.WorkshopClock";
    static props = {};

    setup() {
        // useState wraps the object in a Proxy: assigning to any key on
        // this.state re-renders the component. A plain `this.count = 0`
        // would update the value and change nothing on screen.
        this.state = useState({ openOrders: 0, now: this.formatNow() });
        this.orm = useService("orm");

        // onWillStart is async and runs BEFORE the first render, so the
        // component never flashes a wrong number on its way to the right one.
        onWillStart(async () => {
            this.state.openOrders = await this.countOpenOrders();
        });

        this.timer = setInterval(() => {
            this.state.now = this.formatNow();
        }, 1000);
        // Without this the interval keeps firing after the component is gone,
        // writing to a dead state object forever. Every setInterval in a
        // component needs its matching onWillUnmount.
        onWillUnmount(() => clearInterval(this.timer));
    }

    formatNow() {
        return new Date().toLocaleTimeString();
    }

    countOpenOrders() {
        return this.orm.searchCount("librefleet.service.order", [
            ["stage", "not in", ["done", "cancelled"]],
        ]);
    }

    async onRefresh() {
        this.state.openOrders = await this.countOpenOrders();
    }
}

export const workshopClockItem = { Component: WorkshopClock };

registry.category("systray").add("librefleet.WorkshopClock", workshopClockItem, {
    sequence: 1,
});
