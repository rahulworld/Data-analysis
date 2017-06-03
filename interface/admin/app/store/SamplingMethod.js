/*
 * File: app/store/Constraint.js
 *
 * This file was generated by Ext Designer version 1.2.3.
 * http://www.sencha.com/products/designer/
 *
 * This file will be auto-generated each and everytime you export.
 *
 * Do NOT hand edit this file.
 */

Ext.define('istsos.store.SamplingMethod', {
    extend: 'Ext.data.Store',

    constructor: function(cfg) {
        var me = this;
        cfg = cfg || {};
        me.callParent([Ext.apply({
            storeId: 'samplingmethod',
            data: [
                {
                    name: 'max',
                    'value': 'max'
                },
                {
                    'name': 'min',
                    'value': 'min'
                },
                {
                    'name': 'first',
                    'value': 'first'
                },
                {
                    'name': 'last',
                    'value': 'last'
                },
                {
                    'name': 'median',
                    'value': 'median'
                },
                {
                    'name': 'sum',
                    'value': 'sum'
                }
                
            ],
            proxy: {
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data'
                }
            },
            fields: [
                {
                    name: 'name'
                },
                {
                    name: 'value'
                }
            ]
        }, cfg)]);
    }
});