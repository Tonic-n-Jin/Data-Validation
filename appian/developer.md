# Appian Oracle ↔ DOCX Service

_Developer Guide_

- [Appian Oracle ↔ DOCX Service](#appian-oracle--docx-service)
  - [Architecture](#architecture)
  - [Developer checklist](#developer-checklist)
    - [Language / framework](#language--framework)
    - [Template engineering](#template-engineering)
    - [Mapping config](#mapping-config)
    - [Service endpoints](#service-endpoints)
    - [Appian side](#appian-side)
    - [Security](#security)
    - [Testing](#testing)
    - [CI/CD \& ops](#cicd--ops)
  - [Open questions](#open-questions)
  - [Sources](#sources)

## Architecture

Build one stateless service that handles both directions using Word content controls, and let Appian own every Oracle read and write.

```drawio
<mxfile>
  <diagram id="N7etNbUy-QzmTKiSEa5l" name="Page-1">
    <mxGraphModel dx="1563" dy="1915" grid="1" gridSize="10" guides="1" tooltips="0" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="EtQeLVshjQwynMN0FD_z-0" />
        <mxCell id="EtQeLVshjQwynMN0FD_z-1" parent="EtQeLVshjQwynMN0FD_z-0" />
        <UserObject label="" mermaidData="{&#xa;  &quot;data&quot;: &quot;flowchart LR\n    oracle[\&quot;Oracle DB&lt;br/&gt;&lt;small&gt;Record tables&lt;/small&gt;\&quot;]\n    appian[\&quot;Appian app&lt;br/&gt;&lt;br/&gt;Button 1: Generate&lt;br/&gt;&lt;br/&gt;Button 2: Upload&lt;br/&gt;&lt;small&gt;Staging + diff review&lt;/small&gt;\&quot;]\n    service[\&quot;DOCX service&lt;br/&gt;&lt;small&gt;Stateless&lt;br/&gt;No DB credentials&lt;/small&gt;&lt;br/&gt;&lt;br/&gt;POST /generate&lt;br/&gt;&lt;br/&gt;POST /parse\&quot;]\n    mapping[\&quot;Mapping config&lt;br/&gt;&lt;small&gt;Shared by both&lt;/small&gt;\&quot;]\n\n    oracle --&gt;|\&quot;read record\&quot;| appian\n    appian --&gt;|\&quot;record JSON\&quot;| service\n    service --&gt;|\&quot;.docx\&quot;| appian\n    appian --&gt;|\&quot;uploaded .docx\&quot;| service\n    service --&gt;|\&quot;fields JSON\&quot;| appian\n    appian --&gt;|\&quot;confirmed write\&quot;| oracle\n    service --- mapping&quot;,&#xa;  &quot;config&quot;: null&#xa;}" id="0WWgWhlUDSEcINB15WXH-0">
          <mxCell connectable="0" parent="EtQeLVshjQwynMN0FD_z-1" style="group;transparentBounds=1;editIcon=1;lockedGroup=0;groupPadding=10;" vertex="1">
            <mxGeometry as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Oracle DB&#xa;&lt;small&gt;Record tables&lt;/small&gt;" mermaidId="n:oracle" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Oracle DB&#xa;&lt;small&gt;Record tables&lt;/small&gt;" id="EtQeLVshjQwynMN0FD_z-2">
          <mxCell parent="0WWgWhlUDSEcINB15WXH-0" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="73" width="275" x="10" y="58" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Appian app&#xa;&#xa;Button 1: Generate&#xa;&#xa;Button 2: Upload&#xa;&lt;small&gt;Staging + diff review&lt;/small&gt;" mermaidId="n:appian" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Appian app&#xa;&#xa;Button 1: Generate&#xa;&#xa;Button 2: Upload&#xa;&lt;small&gt;Staging + diff review&lt;/small&gt;" id="EtQeLVshjQwynMN0FD_z-3">
          <mxCell parent="0WWgWhlUDSEcINB15WXH-0" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="150" width="325" x="450" y="20" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="DOCX service&#xa;&lt;small&gt;Stateless&#xa;No DB credentials&lt;/small&gt;&#xa;&#xa;POST /generate&#xa;&#xa;POST /parse" mermaidId="n:service" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="DOCX service&#xa;&lt;small&gt;Stateless&#xa;No DB credentials&lt;/small&gt;&#xa;&#xa;POST /generate&#xa;&#xa;POST /parse" id="EtQeLVshjQwynMN0FD_z-4">
          <mxCell parent="0WWgWhlUDSEcINB15WXH-0" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="169" width="250" x="935" y="10" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Mapping config&#xa;&lt;small&gt;Shared by both&lt;/small&gt;" mermaidId="n:mapping" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Mapping config&#xa;&lt;small&gt;Shared by both&lt;/small&gt;" id="EtQeLVshjQwynMN0FD_z-5">
          <mxCell parent="0WWgWhlUDSEcINB15WXH-0" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="73" width="285" x="1235" y="58" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="read record" mermaidId="e:oracle-&gt;appian#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.678082191780822;entryX=0;entryY=0.5866666666666667;curved=1;exitX=1;exitY=0.68;entryX=0;entryY=0.59;" mermaidBaseValue="read record" id="EtQeLVshjQwynMN0FD_z-6">
          <mxCell edge="1" parent="0WWgWhlUDSEcINB15WXH-0" source="EtQeLVshjQwynMN0FD_z-2" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.68;entryX=0;entryY=0.59;" target="EtQeLVshjQwynMN0FD_z-3">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="368" y="149" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="record JSON" mermaidId="e:appian-&gt;service#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5866666666666667;entryX=0;entryY=0.5769230769230769;curved=1;exitX=1;exitY=0.59;entryX=0;entryY=0.58;" mermaidBaseValue="record JSON" id="EtQeLVshjQwynMN0FD_z-7">
          <mxCell edge="1" parent="0WWgWhlUDSEcINB15WXH-0" source="EtQeLVshjQwynMN0FD_z-3" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.59;entryX=0;entryY=0.58;" target="EtQeLVshjQwynMN0FD_z-4">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="855" y="151" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label=".docx" mermaidId="e:service-&gt;appian#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.5769230769230769;entryX=1;entryY=0.5866666666666667;curved=1;exitX=0;exitY=0.58;entryX=1;entryY=0.59;" mermaidBaseValue=".docx" id="EtQeLVshjQwynMN0FD_z-8">
          <mxCell edge="1" parent="0WWgWhlUDSEcINB15WXH-0" source="EtQeLVshjQwynMN0FD_z-4" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.58;entryX=1;entryY=0.59;" target="EtQeLVshjQwynMN0FD_z-3">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="855" y="140" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="uploaded .docx" mermaidId="e:appian-&gt;service#1" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5866666666666667;entryX=0;entryY=0.5769230769230769;curved=1;exitX=1;exitY=0.59;entryX=0;entryY=0.58;" mermaidBaseValue="uploaded .docx" id="EtQeLVshjQwynMN0FD_z-9">
          <mxCell edge="1" parent="0WWgWhlUDSEcINB15WXH-0" source="EtQeLVshjQwynMN0FD_z-3" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.59;entryX=0;entryY=0.58;" target="EtQeLVshjQwynMN0FD_z-4">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="855" y="162" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="fields JSON" mermaidId="e:service-&gt;appian#1" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.4230769230769231;entryX=1;entryY=0.41333333333333333;curved=1;exitX=0;exitY=0.42;entryX=1;entryY=0.41;" mermaidBaseValue="fields JSON" id="EtQeLVshjQwynMN0FD_z-10">
          <mxCell edge="1" parent="0WWgWhlUDSEcINB15WXH-0" source="EtQeLVshjQwynMN0FD_z-4" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.42;entryX=1;entryY=0.41;" target="EtQeLVshjQwynMN0FD_z-3">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="855" y="43" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="confirmed write" mermaidId="e:appian-&gt;oracle#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.41333333333333333;entryX=1;entryY=0.3219178082191781;curved=1;exitX=0;exitY=0.41;entryX=1;entryY=0.32;" mermaidBaseValue="confirmed write" id="EtQeLVshjQwynMN0FD_z-11">
          <mxCell edge="1" parent="0WWgWhlUDSEcINB15WXH-0" source="EtQeLVshjQwynMN0FD_z-3" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.41;entryX=1;entryY=0.32;" target="EtQeLVshjQwynMN0FD_z-2">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="368" y="25" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="" mermaidId="e:service-&gt;mapping#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=none;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.51;" mermaidBaseValue="" id="EtQeLVshjQwynMN0FD_z-12">
          <mxCell edge="1" parent="0WWgWhlUDSEcINB15WXH-0" source="EtQeLVshjQwynMN0FD_z-4" style="curved=1;startArrow=none;endArrow=none;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.51;" target="EtQeLVshjQwynMN0FD_z-5">
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

## Developer checklist

The default is Java with docx4j. Choose by what your enterprise already hosts and supports.

### Language / framework

| Option                                | Fit for this problem                                                                                                                                                                   | Watch-outs                                                                                                                                     |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Java 17/21 + docx4j                   | Best fit for an Appian shop: Appian plugins are Java, and docx4j has first-class content control and custom XML data binding. Ships as an Appian plugin or a Spring Boot REST service. | Heavier library; plugin deploys depend on the Appian admins                                                                                    |
| .NET 8 + Open XML SDK                 | Most complete content control support                                                                                                                                                  | Only if you're a Microsoft-hosted shop                                                                                                         |
| Python + FastAPI + python-docx + lxml | Workable; matches the team's Python skills                                                                                                                                             | python-docx has no content control API, so you work on the raw XML with lxml. Avoid docxtpl: its tags are consumed on render, like `###` keys. |

- [ ] Pick the language and record the decision as an ADR
- [ ] Pick the hosting: Appian plugin (no extra infrastructure, but tied to Appian admin deploys and more fragile on upgrades) vs. a standalone REST service via Connected System + Integration (independent CI/CD; needs hosting, auth, a network route). Lean REST unless infra blocks it.

### Template engineering

- [ ] Build the template with Developer tab → content controls (Tag = field key, Title = human label)
- [ ] Lock non-editable controls (cannot be deleted / contents cannot be edited)
- [ ] Repeating tables: repeating section content controls, with a hidden row-ID control per row
- [ ] Custom document properties: `template_id`, `template_version`, `record_id`, `row_version` / last-modified timestamp (Appian's free Read Office Doc Properties plugin can read these for routing)
- [ ] Store templates in Appian Document Management, versioned, with a constant pointing to the active one

### Mapping config

- [ ] One source of truth (Oracle config table or versioned JSON in the repo) used by both endpoints
- [ ] Per-field formatter/parser pairs, unit-tested for symmetry: `parse(format(x)) == x`

### Service endpoints

- [ ] `POST /generate`: template id + record JSON → .docx bytes (Base64 for Appian)
- [ ] `POST /parse`: .docx → `{record_id, template_version, fields{}, rows[], errors[]}`
- [ ] `GET /health`, plus a version endpoint
- [ ] Stateless: no DB access, no files left on disk
- [ ] Reject a template or version mismatch, missing required tags, or duplicate tags
- [ ] Ignore anything typed outside a content control, and say so in the user guide

### Appian side

- [ ] Connected System with your enterprise's auth standard (mTLS, an OAuth client credentials grant, or an API key)
- [ ] Integration objects for generate and parse; handle document ↔ Base64 conversion
- [ ] Upload flow: file upload → parse → staging CDT → diff interface → user confirms → write in a single transaction
- [ ] Concurrency check: compare the doc's `row_version` with the current row before writing
- [ ] Audit writes: who, when, field, old value, new value

### Security

- [ ] Validate file type by content, not extension; reject macro-enabled files; enforce a size limit
- [ ] Harden the XML parser (disable external entities, i.e. XXE)
- [ ] No PII in logs; correlation IDs only

### Testing

- [ ] Unit tests: each formatter/parser pair and each validation rule
- [ ] Round-trip tests: generate → parse → assert equality, for every template version
- [ ] Fixture docs actually edited in Word, since Word rewrites the XML (rsids, run splits) in ways a generated fixture won't show
- [ ] Negative fixtures: deleted controls, wrong version, stale record, oversized or malformed files

### CI/CD & ops

- [ ] Pipeline: lint → tests → container image or plugin JAR → deploy to dev, test, then prod
- [ ] Template changes go through the same versioning and review as code
- [ ] Structured logs, latency and error metrics, an alert on the parse failure rate
- [ ] Runbook covering a bad template deploy, a service outage (generation goes down too), and a stuck upload

## Open questions

These two answers decide plugin vs. REST service. Settle them with the Appian platform team before committing to a language.

- [ ] Does the platform team allow custom Appian plugins, or require external services instead?
- [ ] Where can an internal REST service be hosted with a network path from the Appian servers?

## Sources

- [MS Word 2007 Doc from Template Smart Service — Appian docs](https://docs.appian.com/suite/help/26.7/Word_Doc_from_Template_Smart_Service.html)
- [Extracting data from MS Word tags — Appian Community](https://community.appian.com/discussions/f/plug-ins/34537/extracting-data-from-ms-word-tags)
- [Read Office Doc Properties — Appian AppMarket](https://appmarket.appian.com/listings/read-office-doc-properties)
