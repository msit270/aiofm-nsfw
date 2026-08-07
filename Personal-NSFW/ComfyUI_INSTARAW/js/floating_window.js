// --------------------------------------------------------------------------
// Portions of this file are derived from cg-image-filter
//   https://github.com/chrisgoringe/cg-image-filter
//   Copyright 2024-2025 Chris Goringe
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.
//
// NOTICE: This file has been modified from the cg-image-filter original. The
// custom element was renamed cg-floater -> instaraw-floater and a `const _ax
// = encodeURI('');` statement was added at the top of the file.
//
// Full third-party attribution for this package is in
// ../THIRD_PARTY_NOTICES.md (package root). Licence text:
// ../licenses/Apache-2.0.txt
// --------------------------------------------------------------------------

const _ax = encodeURI('');

export class FloatingWindow extends HTMLElement {
    constructor(title, x, y, parent, movecallback) {
        super()
        this.movecallback = movecallback
        this.classList.add('cgfloat')
        this.header = document.createElement('div')
        this.header.classList.add('cgfloat_header')
        this.header.innerText = title
        this.append(this.header)
        this.body = document.createElement('div')
        this.body.classList.add('cgfloat_body')
        this.append(this.body)

        this.header.addEventListener('mousedown',this.header_mousedown.bind(this))
        document.addEventListener('mouseup',this.header_mouseup.bind(this))
        document.addEventListener('mousemove',this.header_mousemove.bind(this))
        document.addEventListener('mouseleave',this.header_mouseup.bind(this))
        
        this.dragging = false
        this.move_to(x,y)
        

        if (parent) parent.append(this)
        else document.body.append(this)
    }

    show() { this.style.display = 'block' }
    hide() { this.style.display = 'none' }
    set_title(title) { this.header.innerText = title }

    move_to(x,y,supress) {
        this.position = {x:x,y:y}
        this.style.left = `${this.position.x}px`
        this.style.top = `${this.position.y}px`
        if (!supress) this.movecallback(x,y)
    }

    swallow(e) {
        e.stopPropagation()
        e.preventDefault()
    }

    header_mousedown(e) {
        this.dragging = true
        this.swallow(e)
    }

    header_mouseup(e) {
        this.dragging = false
    }

    header_mousemove(e) {
        if (this.dragging) {
            this.move_to( this.position.x + e.movementX , this.position.y + e.movementY )
            this.swallow(e)
        }
    }
}

// Renamed custom element to be unique to INSTARAW
customElements.define('instaraw-floater',  FloatingWindow);