/*
 * File: app/view/ui/Editor1.js
 *
 * This file was generated by Ext Designer version 1.2.3.
 * http://www.sencha.com/products/designer/
 *
 * This file will be auto-generated each and everytime you export.
 *
 * Do NOT hand edit this file.
 */

Ext.define('istsos.view.ui.Editor1', {
    extend: 'Ext.panel.Panel',
    requires: [
        'istsos.view.ProcedureChart',
        'istsos.view.ProcedureChooser',
        'istsos.view.ProcedureGridEditor'
    ],

    border: 0,
    padding: 0,
    layout: {
        type: 'border'
    },

    initComponent: function() {
        var me = this;

        Ext.applyIf(me, {
            items: [
                {
                    xtype: 'panel',
                    border: 0,
                    layout: {
                        type: 'border'
                    },
                    title: '',
                    region: 'center',
                    items: [
                        {
                            xtype: 'procedurechart',
                            region: 'center'
                        }
                    ]
                },
                {
                    xtype: 'tabpanel',
                    width: 450,
                    layout: {
                        type: 'fit'
                    },
                    title: '',
                    activeTab: 0,
                    region: 'west',
                    items: [
                        {
                            xtype: 'procedurechooser',
                            border: 0,
                            id: 'pchoose',
                            title: 'Choose procedure'
                        },
                        {
                            xtype: 'proceduregrideditor',
                            id: 'proceduregrideditor',
                            title: 'Editor'
                        }
                    ]
                }
            ]
        });

        me.callParent(arguments);
    }
});