/*
 * File: app/view/ui/FormDataQuality.js
 *
 * This file was generated by Ext Designer version 1.2.3.
 * http://www.sencha.com/products/designer/
 *
 * This file will be auto-generated each and everytime you export.
 *
 * Do NOT hand edit this file.
 */

Ext.define('istsos.view.ui.FormDataQuality', {
    extend: 'Ext.panel.Panel',

    border: 0,
    layout: {
        type: 'anchor'
    },
    title: '',

    initComponent: function() {
        var me = this;

        Ext.applyIf(me, {
            items: [
                {
                    xtype: 'form',
                    border: 0,
                    bodyPadding: 10,
                    title: '',
                    items: [
                        {
                            xtype: 'fieldset',
                            title: 'Add new index',
                            items: [
                                {
                                    xtype: 'textfield',
                                    fieldLabel: 'Code',
                                    anchor: '100%'
                                },
                                {
                                    xtype: 'textfield',
                                    fieldLabel: 'Description',
                                    anchor: '100%'
                                }
                            ]
                        }
                    ],
                    dockedItems: [
                        {
                            xtype: 'toolbar',
                            ui: 'footer',
                            anchor: '100%',
                            dock: 'bottom',
                            layout: {
                                pack: 'end',
                                type: 'hbox'
                            },
                            items: [
                                {
                                    xtype: 'button',
                                    text: 'Cancel'
                                },
                                {
                                    xtype: 'button',
                                    text: 'Add'
                                }
                            ]
                        }
                    ]
                },
                {
                    xtype: 'gridpanel',
                    padding: '16 8 0 8',
                    title: 'Quality indexes',
                    store: 'dataQualityStore',
                    viewConfig: {
                        height: 120
                    },
                    columns: [
                        {
                            xtype: 'gridcolumn',
                            dataIndex: 'code',
                            text: 'Code'
                        },
                        {
                            xtype: 'gridcolumn',
                            dataIndex: 'description',
                            text: 'Description'
                        }
                    ]
                }
            ]
        });

        me.callParent(arguments);
    }
});