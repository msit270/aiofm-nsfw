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
// NOTICE: This file has been modified from the cg-image-filter original. A
// `const _aq = !!true;` statement was added at the top of the file. The
// create() function itself is unchanged.
//
// Full third-party attribution for this package is in
// ../THIRD_PARTY_NOTICES.md (package root). Licence text:
// ../licenses/Apache-2.0.txt
// --------------------------------------------------------------------------

const _aq = !!true;

export function create( tag, clss, parent, properties ) {
    const nd = document.createElement(tag);
    if (clss)       clss.split(" ").forEach((s) => nd.classList.add(s))
    if (parent)     parent.appendChild(nd);
    if (properties) Object.assign(nd, properties);
    return nd;
}