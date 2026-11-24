
# Appian Oracle ↔ DOCX Service

_Business Analyst Guide_

- [Appian Oracle ↔ DOCX Service](#appian-oracle--docx-service)
  - [Architecture](#architecture)
  - [Requirements Documentation - Checklists](#requirements-documentation---checklists)
    - [Scope \& actors](#scope--actors)
    - [Template](#template)
    - [Field mapping (one row per field)](#field-mapping-one-row-per-field)
    - [Upload behavior](#upload-behavior)
    - [Security \& compliance](#security--compliance)
    - [Non-functional](#non-functional)
    - [Acceptance](#acceptance)

## Architecture

Build one stateless service that handles both directions using Word content controls, and let Appian own every Oracle read and write.

```drawio
<mxfile>
  <diagram id="aoz3OFD_vLidUeJ9tQi8" name="Page-1">
    <mxGraphModel dx="1563" dy="1915" grid="1" gridSize="10" guides="1" tooltips="0" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <UserObject label="" mermaidData="{&#xa;  &quot;data&quot;: &quot;flowchart LR\r\n    oracle[\&quot;Oracle DB&lt;br/&gt;&lt;small&gt;Record tables&lt;/small&gt;\&quot;]\r\n    appian[\&quot;Appian app&lt;br/&gt;&lt;br/&gt;Button 1: Generate&lt;br/&gt;&lt;br/&gt;Button 2: Upload&lt;br/&gt;&lt;small&gt;Staging + diff review&lt;/small&gt;\&quot;]\r\n    service[\&quot;DOCX service&lt;br/&gt;&lt;small&gt;Stateless&lt;br/&gt;No DB credentials&lt;/small&gt;&lt;br/&gt;&lt;br/&gt;POST /generate&lt;br/&gt;&lt;br/&gt;POST /parse\&quot;]\r\n    mapping[\&quot;Mapping config&lt;br/&gt;&lt;small&gt;Shared by both&lt;/small&gt;\&quot;]\r\n\r\n    oracle --&gt;|\&quot;read record\&quot;| appian\r\n    appian --&gt;|\&quot;record JSON\&quot;| service\r\n    service --&gt;|\&quot;.docx\&quot;| appian\r\n    appian --&gt;|\&quot;uploaded .docx\&quot;| service\r\n    service --&gt;|\&quot;fields JSON\&quot;| appian\r\n    appian --&gt;|\&quot;confirmed write\&quot;| oracle\r\n    service --- mapping&quot;,&#xa;  &quot;config&quot;: null&#xa;}" id="13">
          <mxCell connectable="0" parent="1" style="group;transparentBounds=1;editIcon=1;lockedGroup=0;groupPadding=10;" vertex="1">
            <mxGeometry as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Oracle DB&#xa;&lt;small&gt;Record tables&lt;/small&gt;" mermaidId="n:oracle" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Oracle DB&#xa;&lt;small&gt;Record tables&lt;/small&gt;" id="2">
          <mxCell parent="13" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="73" width="275" x="10" y="58" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Appian app&#xa;&#xa;Button 1: Generate&#xa;&#xa;Button 2: Upload&#xa;&lt;small&gt;Staging + diff review&lt;/small&gt;" mermaidId="n:appian" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Appian app&#xa;&#xa;Button 1: Generate&#xa;&#xa;Button 2: Upload&#xa;&lt;small&gt;Staging + diff review&lt;/small&gt;" id="3">
          <mxCell parent="13" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="150" width="325" x="450" y="20" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="DOCX service&#xa;&lt;small&gt;Stateless&#xa;No DB credentials&lt;/small&gt;&#xa;&#xa;POST /generate&#xa;&#xa;POST /parse" mermaidId="n:service" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="DOCX service&#xa;&lt;small&gt;Stateless&#xa;No DB credentials&lt;/small&gt;&#xa;&#xa;POST /generate&#xa;&#xa;POST /parse" id="4">
          <mxCell parent="13" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="169" width="250" x="935" y="10" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Mapping config&#xa;&lt;small&gt;Shared by both&lt;/small&gt;" mermaidId="n:mapping" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Mapping config&#xa;&lt;small&gt;Shared by both&lt;/small&gt;" id="5">
          <mxCell parent="13" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="73" width="285" x="1235" y="58" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="read record" mermaidId="e:oracle-&gt;appian#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.678082191780822;entryX=0;entryY=0.5866666666666667;curved=1;exitX=1;exitY=0.68;entryX=0;entryY=0.59;" mermaidBaseValue="read record" id="6">
          <mxCell edge="1" parent="13" source="2" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.68;entryX=0;entryY=0.59;" target="3">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="368" y="149" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="record JSON" mermaidId="e:appian-&gt;service#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5866666666666667;entryX=0;entryY=0.5769230769230769;curved=1;exitX=1;exitY=0.59;entryX=0;entryY=0.58;" mermaidBaseValue="record JSON" id="7">
          <mxCell edge="1" parent="13" source="3" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.59;entryX=0;entryY=0.58;" target="4">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="855" y="151" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label=".docx" mermaidId="e:service-&gt;appian#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.5769230769230769;entryX=1;entryY=0.5866666666666667;curved=1;exitX=0;exitY=0.58;entryX=1;entryY=0.59;" mermaidBaseValue=".docx" id="8">
          <mxCell edge="1" parent="13" source="4" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.58;entryX=1;entryY=0.59;" target="3">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="855" y="140" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="uploaded .docx" mermaidId="e:appian-&gt;service#1" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5866666666666667;entryX=0;entryY=0.5769230769230769;curved=1;exitX=1;exitY=0.59;entryX=0;entryY=0.58;" mermaidBaseValue="uploaded .docx" id="9">
          <mxCell edge="1" parent="13" source="3" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.59;entryX=0;entryY=0.58;" target="4">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="855" y="162" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="fields JSON" mermaidId="e:service-&gt;appian#1" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.4230769230769231;entryX=1;entryY=0.41333333333333333;curved=1;exitX=0;exitY=0.42;entryX=1;entryY=0.41;" mermaidBaseValue="fields JSON" id="10">
          <mxCell edge="1" parent="13" source="4" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.42;entryX=1;entryY=0.41;" target="3">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="855" y="43" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="confirmed write" mermaidId="e:appian-&gt;oracle#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.41333333333333333;entryX=1;entryY=0.3219178082191781;curved=1;exitX=0;exitY=0.41;entryX=1;entryY=0.32;" mermaidBaseValue="confirmed write" id="11">
          <mxCell edge="1" parent="13" source="3" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.41;entryX=1;entryY=0.32;" target="2">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="368" y="25" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="" mermaidId="e:service-&gt;mapping#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=none;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.51;" mermaidBaseValue="" id="12">
          <mxCell edge="1" parent="13" source="4" style="curved=1;startArrow=none;endArrow=none;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.51;" target="5">
            <mxGeometry relative="1" as="geometry">
              <Array as="points" />
            </mxGeometry>
          </mxCell>
        </UserObject>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>

```

Button 1 runs along the upper arrows and button 2 along the lower ones. Nothing reaches Oracle until the user confirms the diff.

- **Generation (button 1):** Appian handles this natively with the MS Word 2007 Doc from Template smart service. Template fields are marked with `###key###`.
- **Upload/parse (button 2):** Appian has no native plugin for reading tagged data back out of a .docx.
- **The catch:** the `###key###` markers are replaced on merge, so the generated document has no keys left to parse. Native generation plus custom parsing means two mappings that will drift apart.
- **Recommendation:** one service owns both directions. Each content control's Tag holds the field key, so the same tag marks a field on the way out and on the way back in.
- **Appian keeps the database:** Appian passes record JSON to the service and gets a .docx back. On upload, the service returns JSON and Appian writes it through its records or data store. The service needs no Oracle credentials, and Appian's record security and audit trail stay intact.

## Requirements Documentation - Checklists

The field mapping table is the core artifact. Most other requirements depend on it.

### Scope & actors

- [ ] Which record or entity types the buttons appear on
- [ ] Roles or groups that can generate vs. upload (these may differ)
- [ ] Business trigger and frequency (ad hoc, workflow step, bulk)
- [ ] What happens between download and upload: who edits, offline or not, how long the doc is held

### Template

- [ ] Template owner and change approver
- [ ] Versioning: can several versions be live at once, and are uploads of older versions accepted?
- [ ] Locked regions vs. editable regions
- [ ] Output format: .docx only, or a PDF copy as well
- [ ] Naming convention for generated files

### Field mapping (one row per field)

- [ ] Field key (the content control Tag)
- [ ] Oracle schema.table.column, data type, length or precision, nullability
- [ ] Direction: out only, in only, or both
- [ ] Display format (dates, currency, codes shown as their descriptions)
- [ ] Reverse parse rule (text back to type, description back to code)
- [ ] Repeating sections or tables (child rows), and how inserts, updates and deletes are detected
- [ ] Lookup and reference data validation
- [ ] Business validation rules (ranges, cross-field rules)

### Upload behavior

- [ ] What a blank field means: set to NULL, or no change?
- [ ] Partial vs. full update
- [ ] Concurrency: what happens if the record changed after the doc was generated? (Reject, warn, or merge)
- [ ] Diff or preview shown to the user before commit (strongly recommended)
- [ ] Approval step before the write
- [ ] Error reporting: per-field messages and where they appear
- [ ] Handling of a doc uploaded against the wrong record

### Security & compliance

- [ ] Data classification of the fields (PII, regulated or GxP data)
- [ ] Retention of generated and uploaded docs in Appian Document Management
- [ ] Audit: who, when, old value → new value
- [ ] File restrictions: .docx only, reject .docm and macros, size limit, malware scan
- [ ] Doc protection or encryption requirements

### Non-functional

- [ ] Volume, peak concurrency, latency target for each button
- [ ] Availability and support model (who gets paged)
- [ ] Appian version, hosting (self-managed vs. cloud), network path to the service

### Acceptance

- [ ] Golden test docs: a clean round trip, every field edited, invalid values, wrong template version, stale record, tampered tags