import React, { useState, useMemo, useEffect, useCallback, useRef } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import { ExternalLink, Search, Filter, Download, X, Info, Save } from "lucide-react";
import "./styles.css";

function ProjectUpdateComponent(props) {
  const { args } = props;

  // Data from Python
  const serverProjects = args.projects || [];
  const leadEngineers = args.lead_engineers || [];
  const phaseOptions = args.phase_options || ["Analysis", "Design", "Development", "Testing", "Deployment", "Support"];
  const statusOptions = args.status_options || ["In progress", "Complete", "On hold", "Cancelled"];

  // Local working copy of projects
  const [projects, setProjects] = useState(() => {
    // Sort initially based on the numeric value of project_code descending
    return [...serverProjects].sort((a, b) => {
      const codeA = parseInt((a.project_code || "0").replace(/\\D/g, ""), 10) || 0;
      const codeB = parseInt((b.project_code || "0").replace(/\\D/g, ""), 10) || 0;
      return codeB - codeA;
    });
  });

  // Sync when Python sends new data (e.g., after a save)
  const prevServerRef = useRef(null);
  useEffect(() => {
    const newKey = JSON.stringify(serverProjects);
    if (prevServerRef.current !== newKey) {
      prevServerRef.current = newKey;
      const sorted = [...serverProjects].sort((a, b) => {
        const codeA = parseInt((a.project_code || "0").replace(/\\D/g, ""), 10) || 0;
        const codeB = parseInt((b.project_code || "0").replace(/\\D/g, ""), 10) || 0;
        return codeB - codeA;
      });
      setProjects(sorted);
    }
  }, [serverProjects]);

  // Filter States
  const [filterName, setFilterName] = useState("");
  const [filterCodeMin, setFilterCodeMin] = useState("");
  const [filterCodeMax, setFilterCodeMax] = useState("");
  const [filterLead, setFilterLead] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterPhase, setFilterPhase] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterUpdatedOnly, setFilterUpdatedOnly] = useState(false);

  // Adjust iframe height after each render
  useEffect(() => { Streamlit.setFrameHeight(); });

  // ---- Filtering ----
  const updatedFlagKeys = [
    "project_name_updated", "lead_engineer_updated", "priority_updated",
    "status_updated", "trello_link_updated", "start_date_updated",
    "end_date_updated", "phase_updated", "prototype_link_updated"
  ];

  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      if (filterName && !(p.project_name || "").toLowerCase().includes(filterName.toLowerCase())) return false;
      const code = parseInt(p.project_code, 10);
      if (filterCodeMin && code < parseInt(filterCodeMin, 10)) return false;
      if (filterCodeMax && code > parseInt(filterCodeMax, 10)) return false;
      if (filterLead && p.lead_engineer !== filterLead) return false;
      if (filterPriority && (p.priority || "").toUpperCase() !== filterPriority.toUpperCase()) return false;
      if (filterPhase && p.phase !== filterPhase) return false;
      if (filterStatus && p.status !== filterStatus) return false;
      if (filterUpdatedOnly) {
        const hasUpdate = updatedFlagKeys.some(
          (k) => p[k] === true || p[k] === "true" || p[k] === "True"
        );
        if (!hasUpdate) return false;
      }
      return true;
    });
  }, [projects, filterName, filterCodeMin, filterCodeMax, filterLead, filterPriority, filterPhase, filterStatus, filterUpdatedOnly]);

  const resetFilters = () => {
    setFilterName(""); setFilterCodeMin(""); setFilterCodeMax("");
    setFilterLead(""); setFilterPriority(""); setFilterPhase(""); setFilterStatus("");
    setFilterUpdatedOnly(false);
  };

  // ---- Infinite Scroll ----
  const [displayCount, setDisplayCount] = useState(30);

  // Reset display count when filters or data change
  useEffect(() => {
    setDisplayCount(30);
  }, [filterName, filterCodeMin, filterCodeMax, filterLead, filterPriority, filterPhase, filterStatus, projects]);

  const handleScroll = (e) => {
    const { scrollHeight, scrollTop, clientHeight } = e.target;
    // If scrolled within 50px of the bottom, load more
    if (scrollHeight - scrollTop <= clientHeight + 50) {
      if (displayCount < filteredProjects.length) {
        setDisplayCount(prev => prev + 30);
      }
    }
  };

  // ---- Editing ----
  const handleUpdate = (projectCode, field, value) => {
    setProjects((prev) =>
      prev.map((p) => (p.project_code === projectCode ? { ...p, [field]: value } : p))
    );
  };

  // Check if a field has been edited locally (differs from server data)
  const isDirty = (projectCode, field) => {
    const server = serverProjects.find((p) => p.project_code === projectCode);
    const local = projects.find((p) => p.project_code === projectCode);
    if (!server || !local) return false;
    return String(server[field] ?? "") !== String(local[field] ?? "");
  };

  // Check if a field has the DB _updated flag
  const isDbUpdated = (project, field) => {
    const flag = project[field + "_updated"];
    if (flag === true || flag === "true" || flag === "True") return true;
    return false;
  };

  // Count of locally edited projects
  const editedCount = useMemo(() => {
    return projects.filter((p) => {
      const server = serverProjects.find((sp) => sp.project_code === p.project_code);
      return server && JSON.stringify(server) !== JSON.stringify(p);
    }).length;
  }, [projects, serverProjects]);

  // ---- Save ----
  const handleSave = useCallback(() => {
    const edits = {};
    projects.forEach((p, idx) => {
      const server = serverProjects.find((sp) => sp.project_code === p.project_code);
      if (!server) return;
      const changes = {};
      const editableFields = ["project_name", "lead_engineer", "priority", "start_date", "end_date", "status", "phase", "trello_link", "prototype_link"];
      editableFields.forEach((f) => {
        if (String(server[f] ?? "") !== String(p[f] ?? "")) {
          changes[f] = p[f];
        }
      });
      if (Object.keys(changes).length > 0) {
        edits[p.project_code] = changes;
      }
    });
    if (Object.keys(edits).length > 0) {
      Streamlit.setComponentValue({ action: "save", edits: edits });
    }
  }, [projects, serverProjects]);

  // ---- Export ----
  const handleExportClick = () => {
    Streamlit.setComponentValue({ action: "open_export_modal" });
  };

  // ---- Cell class helpers ----
  const cellInputClass = (projectCode, field, extra = "") => {
    let cls = "pu-cell-input";
    if (extra) cls += " " + extra;
    if (isDirty(projectCode, field)) cls += " dirty";
    const proj = projects.find(p => p.project_code === projectCode);
    if (proj && !isDirty(projectCode, field) && isDbUpdated(proj, field)) cls += " db-updated";
    return cls;
  };

  const cellSelectClass = (projectCode, field, extra = "") => {
    let cls = "pu-cell-select";
    if (extra) cls += " " + extra;
    if (isDirty(projectCode, field)) cls += " dirty";
    const proj = projects.find(p => p.project_code === projectCode);
    if (proj && !isDirty(projectCode, field) && isDbUpdated(proj, field)) cls += " db-updated";
    return cls;
  };

  const statusClass = (status) => {
    if (status === "Complete") return "status-complete";
    if (status === "In progress") return "status-progress";
    if (status === "On hold") return "status-hold";
    if (status === "Cancelled") return "status-cancel";
    return "";
  };

  // ---- Render ----
  return (
    <div className="pu-page">
      <div className="pu-container">

        {/* Header */}
        <div className="pu-header">
          <h1 className="pu-title">Project Attributes</h1>
          <div className="pu-header-actions">
            <span className="pu-count-label">
              Showing {filteredProjects.length} of {projects.length} projects
            </span>
            {editedCount > 0 && (
              <button className="pu-save-btn" onClick={handleSave}>
                <Save size={16} /> Save Changes ({editedCount})
              </button>
            )}
            <button className="pu-export-btn" onClick={handleExportClick}>
              <Download size={16} /> Export
            </button>
          </div>
        </div>

        {/* Unsaved Changes Banner */}
        {editedCount > 0 && (
          <div className="pu-unsaved-banner">
            <span>⚠ You have {editedCount} unsaved change(s).</span>
            <button className="pu-save-btn" onClick={handleSave} style={{padding: "0.35rem 0.75rem", fontSize: "0.8rem"}}>
              <Save size={14} /> Save
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="pu-filters">
          <div className="pu-filters-header">
            <Filter size={18} />
            <span>Filters</span>
          </div>
          <div className="pu-filters-grid">

            {/* Project Name */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Project Name</label>
              <div className="pu-filter-input-wrap">
                <input
                  type="text"
                  placeholder="e.g. Alpha Search..."
                  value={filterName}
                  onChange={(e) => setFilterName(e.target.value)}
                  className="pu-filter-input has-icon"
                />
                <Search size={14} className="pu-filter-search-icon" />
              </div>
            </div>

            {/* Code Range */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Project Code Range</label>
              <div className="pu-filter-code-range">
                <input type="number" placeholder="Min" value={filterCodeMin}
                  onChange={(e) => setFilterCodeMin(e.target.value)} className="pu-filter-input" />
                <span className="pu-code-separator">–</span>
                <input type="number" placeholder="Max" value={filterCodeMax}
                  onChange={(e) => setFilterCodeMax(e.target.value)} className="pu-filter-input" />
              </div>
            </div>

            {/* Lead Engineer */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Lead Engineer</label>
              <select value={filterLead} onChange={(e) => setFilterLead(e.target.value)} className="pu-filter-select">
                <option value="">All Engineers</option>
                {leadEngineers.map((eng) => <option key={eng} value={eng}>{eng}</option>)}
              </select>
            </div>

            {/* Priority */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Priority</label>
              <input type="text" placeholder="e.g. P1, P10" value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
                className="pu-filter-input" style={{textTransform: "uppercase"}} />
            </div>

            {/* Phase */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Phase</label>
              <select value={filterPhase} onChange={(e) => setFilterPhase(e.target.value)} className="pu-filter-select">
                <option value="">All Phases</option>
                {phaseOptions.map((ph) => <option key={ph} value={ph}>{ph}</option>)}
              </select>
            </div>

            {/* Status + Clear */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Status</label>
              <div className="pu-status-row">
                <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="pu-filter-select">
                  <option value="">All Statuses</option>
                  {statusOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <button className="pu-clear-btn" onClick={resetFilters} title="Clear all filters">Clear</button>
              </div>
            </div>

            {/* Updated Records toggle */}
            <div className="pu-filter-group pu-filter-group--full">
              <label className="pu-filter-label">Quick Filter</label>
              <button
                className={`pu-updated-toggle${filterUpdatedOnly ? " active" : ""}`}
                onClick={() => setFilterUpdatedOnly((v) => !v)}
                title="Show only rows with highlighted (updated) fields"
              >
                <span className="pu-updated-dot" />
                Updated Records Only
              </button>
            </div>

          </div>
        </div>

        {/* Data Table */}
        <div className="pu-table-wrapper">
          <div className="pu-table-scroll" onScroll={handleScroll}>
            <table className="pu-table">
              <thead>
                <tr>
                  <th className="center" style={{minWidth:40, width:40}}>#</th>
                  <th style={{minWidth:70, width:70}}>Code</th>
                  <th style={{minWidth:180}}>Project Name</th>
                  <th style={{minWidth:200}}>Lead Engineer</th>
                  <th className="center" style={{minWidth:70, width:70}}>Priority</th>
                  <th style={{minWidth:130}}>Start Date</th>
                  <th style={{minWidth:130}}>End Date</th>
                  <th style={{minWidth:120}}>Status</th>
                  <th style={{minWidth:120}}>Phase</th>
                  <th className="center" style={{minWidth:140}}>Trello</th>
                  <th className="center" style={{minWidth:140}}>Prototype</th>
                </tr>
              </thead>
              <tbody>
                {filteredProjects.length > 0 ? (
                  filteredProjects.slice(0, displayCount).map((project, index) => (
                    <tr key={project.project_code}>
                      <td className="num-col">{index + 1}</td>
                      <td className="code-col">{project.project_code}</td>

                      {/* Project Name */}
                      <td>
                        <input type="text" value={project.project_name || ""}
                          onChange={(e) => handleUpdate(project.project_code, "project_name", e.target.value)}
                          className={cellInputClass(project.project_code, "project_name")}
                          title={project.project_name || ""} />
                      </td>

                      {/* Lead Engineer */}
                      <td>
                        <select value={project.lead_engineer || ""}
                          onChange={(e) => handleUpdate(project.project_code, "lead_engineer", e.target.value)}
                          className={cellSelectClass(project.project_code, "lead_engineer")}>
                          <option value="">—</option>
                          {leadEngineers.map((eng) => <option key={eng} value={eng}>{eng}</option>)}
                        </select>
                      </td>

                      {/* Priority */}
                      <td>
                        <input type="text" value={project.priority || ""}
                          onChange={(e) => handleUpdate(project.project_code, "priority", e.target.value.toUpperCase())}
                          maxLength={4}
                          className={cellInputClass(project.project_code, "priority", "priority-field")}
                          title="P followed by 1-2 digits (e.g. P1, P10)" />
                      </td>

                      {/* Start Date */}
                      <td>
                        <input type="date" value={project.start_date || ""}
                          onChange={(e) => handleUpdate(project.project_code, "start_date", e.target.value)}
                          className={cellInputClass(project.project_code, "start_date", "date-field")} />
                      </td>

                      {/* End Date */}
                      <td>
                        <input type="date" value={project.end_date || ""}
                          onChange={(e) => handleUpdate(project.project_code, "end_date", e.target.value)}
                          className={cellInputClass(project.project_code, "end_date", "date-field")} />
                      </td>

                      {/* Status */}
                      <td>
                        <select value={project.status || "In progress"}
                          onChange={(e) => handleUpdate(project.project_code, "status", e.target.value)}
                          className={cellSelectClass(project.project_code, "status")}>
                          {statusOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                        </select>
                      </td>

                      {/* Phase */}
                      <td>
                        <select value={project.phase || "Analysis"}
                          onChange={(e) => handleUpdate(project.project_code, "phase", e.target.value)}
                          className={cellSelectClass(project.project_code, "phase")}>
                          {phaseOptions.map((ph) => <option key={ph} value={ph}>{ph}</option>)}
                        </select>
                      </td>

                      {/* Trello */}
                      <td>
                        <div className="pu-link-cell">
                          <input type="text" value={project.trello_link || ""}
                            onChange={(e) => handleUpdate(project.project_code, "trello_link", e.target.value)}
                            className={cellInputClass(project.project_code, "trello_link", "url-field")}
                            placeholder="Trello URL" />
                          {project.trello_link && (
                            <a href={project.trello_link} target="_blank" rel="noopener noreferrer"
                              className="pu-external-link" title="Open Trello">
                              <ExternalLink size={14} />
                            </a>
                          )}
                        </div>
                      </td>

                      {/* Prototype */}
                      <td>
                        <div className="pu-link-cell">
                          <input type="text" value={project.prototype_link || ""}
                            onChange={(e) => handleUpdate(project.project_code, "prototype_link", e.target.value)}
                            className={cellInputClass(project.project_code, "prototype_link", "url-field")}
                            placeholder="Prototype URL" />
                          {project.prototype_link && (
                            <a href={project.prototype_link} target="_blank" rel="noopener noreferrer"
                              className="pu-external-link purple" title="Open Prototype">
                              <ExternalLink size={14} />
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="11">
                      <div className="pu-empty-state">
                        <Search size={24} />
                        <p>No projects match your current filters.</p>
                        <button className="pu-empty-link" onClick={resetFilters}>Clear filters</button>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}

export default withStreamlitConnection(ProjectUpdateComponent);
