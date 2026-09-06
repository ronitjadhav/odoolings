import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { formatFloat } from "@web/views/fields/formatters";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class MarginField extends Component {
    static template = "librefleet.MarginField";
    // Spreading standardFieldProps is not optional: the view engine always
    // passes name/record/readonly/id, and OWL's prop validation rejects any
    // prop the component did not declare.
    static props = { ...standardFieldProps };

    get value() {
        // Every field widget reads its own value the same way: the record is
        // handed to it as a prop, and props.name says which field it is bound
        // to. That indirection is what lets one widget serve many fields.
        return this.props.record.data[this.props.name];
    }

    get formattedValue() {
        return formatFloat(this.value, {
            field: this.props.record.fields[this.props.name],
        });
    }

    get isLoss() {
        return this.value < 0;
    }

    get cssClass() {
        return this.isLoss ? "text-danger fw-bold" : "text-success";
    }

    get iconClass() {
        return this.isLoss ? "fa-arrow-down" : "fa-arrow-up";
    }
}

export const marginField = {
    component: MarginField,
    displayName: _t("Workshop Margin"),
    // Declaring the types this widget understands is what makes Odoo refuse
    // it on, say, a Char field, instead of rendering something broken.
    supportedTypes: ["float", "monetary"],
};

registry.category("fields").add("librefleet_margin", marginField);
