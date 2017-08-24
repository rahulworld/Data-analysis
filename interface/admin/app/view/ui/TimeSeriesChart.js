/*
 * File: app/view/ui/ProcedureChart.js
 *
 * This file was generated by Ext Designer version 1.2.3.
 * http://www.sencha.com/products/designer/
 *
 * This file will be auto-generated each and everytime you export.
 *
 * Do NOT hand edit this file.
 */

Ext.define('istsos.view.ui.TimeSeriesChart', {
    extend: 'Ext.panel.Panel',

    border: 0,
    id: 'serieschartpanel',
    layout: {
        type: 'border'
    },
    title: '',

    initComponent: function() {
        var me = this;

        Ext.applyIf(me, {
            items: [
                {
                    xtype: 'panel',
                    border: 0,
                    style: 'background-color: white;',
                    id:'chartdraw',
                    layout: {
                        type: 'fit'
                    },
                    title: '',
                    region: 'center',
                    items: [
                        {
                            xtype: 'panel',
                            border: 0,
                            id: "chartSeries",
                            layout: {
                                type: 'fit'
                            },
                            bodyCls: 'viewerChart',
                            title: ''
                        },
                        {
                            xtype: 'panel',
                            border: 0,
                            hidden:true,
                            id: "show_result",
                            layout: {
                                type: 'fit'
                            },
                            overflowY: 'scroll',
                            autoScroll: true,
                            height:400,
                            bodyCls: 'viewerChart',
                            title: ''
                        }
                    ]
                }
            ]
        });

        me.callParent(arguments);
    }
});