import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { FormController } from "@web/views/form/form_controller";

// A patch is GLOBAL and unconditional: this runs on every form view in the
// entire web client, for every model, in every app. There is no way to scope
// a patch at registration time, so the scoping has to happen inside the
// method (the resModel guard below). Forget it and you have changed how
// Sales, Invoicing and Settings behave too.
patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
    },

    async onWillSaveRecord(record) {
        const result = await super.onWillSaveRecord(...arguments);
        if (record.resModel === "librefleet.service.order" && record.data.margin < 0) {
            this.notification.add(
                _t("This order is being saved at a loss of %s.", record.data.margin.toFixed(2)),
                { type: "warning", title: _t("Negative margin") }
            );
        }
        // Returning false from this hook cancels the save. We deliberately do
        // not: chapter 20's wizard is where the hard block lives, and a UI
        // patch is the wrong place to enforce a business rule (an import or
        // an RPC call would bypass it entirely).
        return result;
    },
});
