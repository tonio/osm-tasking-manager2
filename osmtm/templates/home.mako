# -*- coding: utf-8 -*-
<%inherit file="base.mako"/>
<%block name="header">
<div class="navbar-brand">OSM Tasking Manager</div>
</%block>
<%block name="content">
<%
base_url = request.route_path('home')
priorities = [_('urgent'), _('high'), _('medium'), _('low')]

sorts = [('priority', 'asc', _('High priority first')),
         ('created', 'desc', _('Creation date')),
         ('last_update', 'desc', _('Last update'))]
%>
<div class="container">
  <div class="col-md-6">
    <h3>Projects</h3>
    <%
        qs = dict(request.GET)

        sort_by = qs.get('sort_by', 'priority')
        direction = qs.get('direction', 'asc')
        button_text = ''
        for sort in sorts:
            if sort[0] == sort_by and sort[1] == direction:
                button_text = sort[2]
        endfor
    %>
    <form class="form-inline" role="form"
          action="${request.current_route_url()}"
          method="GET">

      <input type="hidden" name="sort_by"
             value="${request.params.get('sort_by', 'priority')}">
      <input type="hidden" name="direction"
             value="${request.params.get('direction', 'asc')}">

      <div class="form-group left-inner-addon">
        <i class="glyphicon glyphicon-search text-muted"></i>
        <input type="search" class="form-control input-sm"
               name="search" placeholder="${_('Search')}"
               value="${request.params.get('search', '')}">
      </div>
      <div class="btn-group pull-right">
        <button type="button" class="btn btn-default btn-sm dropdown-toggle"
                data-toggle="dropdown">
          ${_('Sort by:')} <strong>${button_text}</strong>
          <span class="caret"></span>
        </button>
        <ul class="dropdown-menu" role="menu">
          % for sort in sorts:
            <%
              qs['sort_by'] = sort[0]
              qs['direction'] = sort[1]
            %>
            <li>
              <a href="${request.current_route_url(_query=qs.items())}">
                ${sort[2]}
              </a>
            </li>
          % endfor
        </ul>
      </div>
    </form>
    <hr>
    % if paginator.items:
        % for project in paginator.items:
          ${project_block(project=project, base_url=base_url,
                          priorities=priorities)}
        % endfor
        ${paginator.pager()}
    % endif
  </div>
  <div class="col-md-6">
    <h3>New to the Tasking Manager?</h3>
    <p>What is this Tasking Manager all about?</p>
  </div>
</div>
</%block>

<%def name="project_block(project, base_url, priorities)">
<%
    if request.locale_name:
        project.locale = request.locale_name
    priority = priorities[project.priority]
%>
<div class="project well">
  <ul class="nav project-stats">
    <li>
      <table>
        <tr>
          <td>
            <div class="progress">
              <div style="width: ${project.done}%;" class="progress-bar progress-bar-warning"></div>
              <div style="width: ${project.validated}%;" class="progress-bar progress-bar-success"></div>
            </div>
          </td>
          <td>&nbsp;${project.done + project.validated}%</td>
        </tr>
      </table>
    </li>
  </ul>
  <h4><a href="${base_url}project/${project.id}">#${project.id} ${project.name}</a>
  </h4>
  <div class="clear"></div>
  <div class="world_map">
    % if project.area:
    <%
        from geoalchemy2 import shape
        centroid = shape.to_shape(project.area.centroid)
    %>
    <div style="top: ${(-centroid.y + 90) * 60 / 180 - 1}px; left: ${(centroid.x + 180) * 120 / 360 - 1}px;" class="marker"></div>
    % endif
  </div>
  ${project.short_description}
  <div class="clear"></div>
  <small class="text-muted">
    % if project.private:
    <span class="glyphicon glyphicon-lock"
          title="${_('Access to this project is limited')}"></span> -
    % endif
    <span>${_('Created by')} ${project.author.username if project.author else ''}</span> -
    <span>${_('Updated')} <span class="timeago" title="${project.last_update}Z"></span></span> -
    <span>${_('Priority:')} ${priority}</span>
  </small>
</div>
</%def>
