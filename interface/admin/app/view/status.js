/*
 * File: app/view/status.js
 * Date: Fri Apr 20 2012 10:13:38 GMT+0200 (CEST)
 *
 * This file was generated by Ext Designer version 1.2.2.
 * http://www.sencha.com/products/designer/
 *
 * This file will be generated the first time you export.
 *
 * You should implement event handling and custom methods in this
 * class.
 */

Ext.define('istsos.view.status', {
    extend: 'istsos.view.ui.status',

    initComponent: function() {
        var me = this;
        var procs = Ext.create('istsos.store.serverstatus');
        me.callParent(arguments);
        var colorize = function (val) {
            if (val == 'active') {
                return '<span style="color:green;">' + val + '</span>';
            } else if (val == 'up') {
                return '<span style="color:green;">' + val + '</span>';
            } else {
                return '<span style="color:red;">' + val + '</span>';
            }
            return val;
        };
        Ext.getCmp('colDatabase').renderer = colorize;
        Ext.getCmp('colAvailability').renderer = colorize;
        var requests = function (val) {
            if (val) {
                return '<img src="images/icon/ok.svg" height="16px"/>';
            } else {
                return '<img src="images/icon/ko.svg" height="16px"/>';
            }
            return val;
        };
        Ext.getCmp('colGetcapabilities').renderer = requests;
        Ext.getCmp('colDescribesensor').renderer = requests;
        Ext.getCmp('colGetobservation').renderer = requests;
        Ext.getCmp('colGetfeatureofinterest').renderer = requests;
        Ext.getCmp('colInsertobservation').renderer = requests;
        Ext.getCmp('colRegistersensor').renderer = requests;
    },
    operationLoad: function(){
        Ext.getCmp('webadmincmp').showMask("Loading status info..")
        Ext.Ajax.request({
            url: Ext.String.format("{0}/istsos/operations/status", wa.url),
            scope: this,
            method: "GET",
            success: function(response){
                var json = Ext.decode(response.responseText);
                if (json.success) {
                    this.istForm.getStore().loadData(json.data);
                }
                //this.mask.hide();
                Ext.getCmp('webadmincmp').hideMask();
            }
        });
    }
});