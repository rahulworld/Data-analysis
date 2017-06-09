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


/*
 * https://github.com/sterlingwes/RandomColor
 */
(function(root,factory){
    if(typeof exports==='object'){
        module.exports=factory;
    }else if(typeof define==='function'&&define.amd){
        define(factory);
    }else{
        root.RColor=factory();
    }
}(this,function(){
    var RColor=function(){
        this.hue=Math.random(),this.goldenRatio=0.618033988749895;
    };
    RColor.prototype.hsvToRgb=function(h,s,v){
        var h_i=Math.floor(h*6),f=h*6- h_i,p=v*(1-s),q=v*(1-f*s),t=v*(1-(1-f)*s),r=255,g=255,b=255;
        switch(h_i){
            case 0:
                r=v,g=t,b=p;
                break;
            case 1:
                r=q,g=v,b=p;
                break;
            case 2:
                r=p,g=v,b=t;
                break;
            case 3:
                r=p,g=q,b=v;
                break;
            case 4:
                r=t,g=p,b=v;
                break;
            case 5:
                r=v,g=p,b=q;
                break;
        }
        return[Math.floor(r*256),Math.floor(g*256),Math.floor(b*256)];
    };
    RColor.prototype.get=function(hex,saturation,value){
        this.hue+=this.goldenRatio;
        this.hue%=1;
        if(typeof saturation!=="number")saturation=0.5;
        if(typeof value!=="number")value=0.95;
        var rgb=this.hsvToRgb(this.hue,saturation,value);
        if(hex)
            return"#"+rgb[0].toString(16)+rgb[1].toString(16)+rgb[2].toString(16);else
            return rgb;
    };
    return RColor;
}));

Ext.define('istsos.view.ProcessTimeTab', {
    extend: 'istsos.view.ui.ProcessTimeTab',
    alias: 'widget.ProcessTab',

    initComponent: function() {

        var me = this;
        this.color = new RColor;

        this.addEvents({
            // "procedureAdded" : true,
            // "procedureRemoved" : true,
            // "serviceSelected" : true,
            // "offeringSelected" : true,
            // "procedureSelected" : true
        });
});
