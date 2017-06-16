/**
 * istSOS WebAdmin - Istituto Scienze della Terra
 * Copyright (C) 2013 Massimiliano Cannata, Milan Antonovic
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 */

Ext.define('istsos.view.TimeSeriesChart', {
    extend: 'istsos.view.ui.TimeSeriesChart',
    alias: 'widget.timeserieschart',

    initComponent: function() {
        var me = this;
        this.procedures = {};
        chart=Ext.getCmp('chartCnt12');
        var myDiv = document.getElementsByClassName('chartCnt12');
        // var g=new Dygraph(
        //     myDiv,
        //     "Date,Temperature\n" +
        //     "2008-05-07,15\n" +
        //     "2008-05-08,20\n" +
        //     "2008-05-09,40\n",
        //     {
                
        //     }
        // );
        me.callParent(arguments);
        // this.addEvents('queueLoaded','observedPropertyIsSet','clickCallback','pointClickCallback', 'seriesSelected', 'underlayCallback');
    }
});
