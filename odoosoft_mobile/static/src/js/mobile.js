/**
 * Created by cysnake4713 on 15-4-10.
 */
openerp.odoosoft_mobile = function (instance) {

    var _lt = instance.web._lt;
    var _t = instance.web._t;
    var Qweb = instance.web.qweb;

    instance.web.is_use_mobile = function () {
        if (window.location.pathname.indexOf('/mobile') == 0) {
            return true
        } else {
            return false
        }
    };

    instance.web.WebClient.include({
        bind_hashchange: function () {
            var self = this;
            $(window).bind('hashchange', this.on_hashchange);

            var state = $.bbq.getState(true);
            if (_.isEmpty(state) || state.action == "login") {
                self.menu.is_bound.done(function () {
                    new instance.web.Model("res.users").call("read", [self.session.uid, ["action_id"]]).done(function (data) {
                        if (data.action_id) {
                            self.action_manager.do_action(data.action_id[0]);
                            self.menu.open_action(data.action_id[0]);
                        } else {
                            var first_menu_id = self.menu.$el.find("[data-action-id]:first").data("menu");
                            if (first_menu_id) {
                                self.menu.menu_click(first_menu_id);
                            }
                        }
                    });
                });
            } else {
                $(window).trigger('hashchange');
            }
        }
    });

    instance.web.logout = function () {
        if (instance.web.is_use_mobile()) {
            instance.web.redirect('/mobile/session/logout');
        } else {
            instance.web.redirect('/web/session/logout');
        }
    };

    instance.web.MobileViewManagerAction = instance.web.ViewManagerAction.extend({
        template: "MobileViewManagerAction"

    });

    instance.web.ActionManager.include({
        ir_actions_act_window: function (action, options) {
            if (instance.web.is_use_mobile()) {
                $('.oe_mobile_waiting_hint').remove();
                var self = this;
                return this.ir_actions_common({
                    widget: function () {
                        return new instance.web.MobileViewManagerAction(self, action);
                    },
                    action: action,
                    klass: 'oe_act_window',
                    post_process: function (widget) {
                        widget.add_breadcrumb({
                            on_reverse_breadcrumb: options.on_reverse_breadcrumb,
                            hide_breadcrumb: options.hide_breadcrumb
                        });
                    }
                }, options);
            } else {
                this._super(action, options);
            }

        }
    });

    instance.web.ListView.include({
        setup_columns: function (fields, grouped) {
            var self = this;
            var registry = instance.web.list.columns;
            this.columns.splice(0, this.columns.length);
            this.columns.push.apply(this.columns,
                _(this.fields_view.arch.children).map(function (field) {
                    var id = field.attrs.name;
                    return registry.for_(id, fields[id], field);
                }));
            if (grouped) {
                this.columns.unshift(
                    new instance.web.list.MetaColumn('_group', _t("Group")));
            }

            var mobile_columns = _.filter(this.columns, function (column) {
                return column.mobile == '1';
            });
            if (instance.web.is_use_mobile()) {
                if (mobile_columns.length > 0) {
                    var invisible_columns = _.filter(this.columns, function (column) {
                        return column.mobile !== '1';
                    });
                    _.each(invisible_columns, function (column) {
                        column.invisible = '1';
                    });
                } else {
                    var visible_columns = _.filter(this.columns, function (column) {
                        return column.invisible !== '1';
                    });
                    _.each(visible_columns.slice(_.min([3, visible_columns.length]), visible_columns.length), function (column) {
                        column.invisible = '1';
                    });
                }
            }

            this.visible_columns = _.filter(this.columns, function (column) {
                return column.invisible !== '1';
            });
            this.aggregate_columns = _(this.visible_columns).invoke('to_aggregate');
        }
    });

    instance.web.list.Column.include({
        init: function (id, tag, attrs) {
            this._super(id, tag, attrs);
            this.mobile = attrs.mobile;
        }
    });

    instance.web.form.FormRenderingEngine.include({
        process_group: function ($group) {
            var self = this;
            var fields = $group.find('field');
            $group.empty();
            fields.appendTo($group);
            $group.children('field').each(function () {
                self.preprocess_field($(this));
            });
            var $new_group = this.render_element('FormRenderingGroup', $group.getAttributes());
            var $table;
            if ($new_group.first().is('table.oe_form_group')) {
                $table = $new_group;
            } else if ($new_group.filter('table.oe_form_group').length) {
                $table = $new_group.filter('table.oe_form_group').first();
            } else {
                $table = $new_group.find('table.oe_form_group').first();
            }

            var $tr, $td,
                cols = parseInt(2, 10),
                row_cols = cols;

            var children = [];
            $group.children().each(function (a, b, c) {
                var $child = $(this);
                var colspan = parseInt($child.attr('colspan') || 1, 10);
                var tagName = $child[0].tagName.toLowerCase();
                var $td = $('<td/>').addClass('oe_form_group_cell').attr('colspan', colspan);
                var newline = tagName === 'newline';

                // Note FME: those classes are used in layout debug mode
                if ($tr && row_cols > 0 && (newline || row_cols < colspan)) {
                    $tr.addClass('oe_form_group_row_incomplete');
                    if (newline) {
                        $tr.addClass('oe_form_group_row_newline');
                    }
                }
                if (newline) {
                    $tr = null;
                    return;
                }
                if (!$tr || row_cols < colspan) {
                    $tr = $('<tr/>').addClass('oe_form_group_row').appendTo($table);
                    row_cols = cols;
                } else if (tagName === 'group') {
                    // When <group> <group/><group/> </group>, we need a spacing between the two groups
                    $td.addClass('oe_group_right');
                }
                row_cols -= colspan;

                // invisibility transfer
                var field_modifiers = JSON.parse($child.attr('modifiers') || '{}');
                var invisible = field_modifiers.invisible;
                self.handle_common_properties($td, $("<dummy>").attr("modifiers", JSON.stringify({invisible: invisible})));

                $tr.append($td.append($child));
                children.push($child[0]);
            });
            if (row_cols && $td) {
                $td.attr('colspan', parseInt($td.attr('colspan'), 10) + row_cols);
            }
            $group.before($new_group).remove();

            $table.find('> tbody > tr').each(function () {
                var to_compute = [],
                    row_cols = cols,
                    total = 100;
                $(this).children().each(function () {
                    var $td = $(this),
                        $child = $td.children(':first');
                    if ($child.attr('cell-class')) {
                        $td.addClass($child.attr('cell-class'));
                    }
                    switch ($child[0].tagName.toLowerCase()) {
                        case 'separator':
                            break;
                        case 'label':
                            if ($child.attr('for')) {
                                $td.attr('width', '1%').addClass('oe_form_group_cell_label');
                                row_cols -= $td.attr('colspan') || 1;
                                total--;
                            }
                            break;
                        default:
                            var width = _.str.trim($child.attr('width') || ''),
                                iwidth = parseInt(width, 10);
                            if (iwidth) {
                                if (width.substr(-1) === '%') {
                                    total -= iwidth;
                                    width = iwidth + '%';
                                } else {
                                    // Absolute width
                                    $td.css('min-width', width + 'px');
                                }
                                $td.attr('width', width);
                                $child.removeAttr('width');
                                row_cols -= $td.attr('colspan') || 1;
                            } else {
                                to_compute.push($td);
                            }

                    }
                });
                if (row_cols) {
                    var unit = Math.floor(total / row_cols);
                    if (!$(this).is('.oe_form_group_row_incomplete')) {
                        _.each(to_compute, function ($td, i) {
                            var width = parseInt($td.attr('colspan'), 10) * unit;
                            $td.attr('width', width + '%');
                            total -= width;
                        });
                    }
                }
            });
            _.each(children, function (el) {
                self.process($(el));
            });
            this.handle_common_properties($new_group, $group);
            return $new_group;
        }
    });

    instance.web.Menu.include({
        menu_click: function (id, needaction) {
            this._super(id, needaction);
            var $item = this.$el.find('a[data-menu=' + id + ']');
            var action_id = $item.data('action-id');
            if (action_id) {
                $('button.navbar-toggle').trigger('click');
            }
        }
    });

    instance.web.FormView.include({
        autofocus: function () {
            if (!instance.web.is_use_mobile()) {
                if (this.get("actual_mode") !== "view" && !this.options.disable_autofocus) {
                    var fields_order = this.fields_order.slice(0);
                    if (this.default_focus_field) {
                        fields_order.unshift(this.default_focus_field.name);
                    }
                    for (var i = 0; i < fields_order.length; i += 1) {
                        var field = this.fields[fields_order[i]];
                        if (!field.get('effective_invisible') && !field.get('effective_readonly') && field.$label) {
                            if (field.focus() !== false) {
                                break;
                            }
                        }
                    }
                }
            }
        }
    });

    if (openerp.im_chat) {
        openerp.im_chat.InstantMessaging.include({
            start: function () {
                if (!instance.web.is_use_mobile()) {
                    this._super();
                }
            }
        });
    }
};
