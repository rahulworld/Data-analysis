# -*- coding: utf-8 -*-
# ===============================================================================
#
#
# Copyright (c) 2015 IST-SUPSI (www.supsi.ch/ist)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# ===============================================================================
"""
    Configuration file

"""
import os

db_path = None
ui_path = os.path.join(os.path.dirname(__file__), 'ui')
gif_path = os.path.join(ui_path, 'images', 'loading.gif')
icon_path = os.path.join(ui_path, 'images', 'mapIcon.png')

oat_layer_name = 'oat_sensors'