from django import template
from django.core.urlresolvers import reverse

register = template.Library()

class MDSDataTemplateNode(template.Node):
    def __init__(self, data_name):
        self.data_var = template.Variable(data_name)
    def render(self, context):
        try:
            data = self.data_var.resolve(context)
            return '<div class="centrecontent">%s</div>' %data.get_view('html')
        except template.VariableDoesNotExist:
            return ''

def display_data(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, data_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return MDSDataTemplateNode(data_name)


register.tag('display_data', display_data)

filter_html = """\
<div class="sidebarcontent">
 <form action="%(submit_url)s">
  <span class="left" title="%(text)s">%(clsname)s</span>
  <span class="right">%(input_str)s<input type="submit" title="add" value="+"/></span>
  <input type="hidden" name="filter" value="%(clsname)s">
  <input type="hidden" name="path" value="%(path)s">%(input_query)s
 </form>
</div>"""


active_filter_html ="""\
<div class="sidebarcontent">
 <form action="%(update_url)s">
  <span class="left" title="%(text)s">%(clsname)s</span>
  <span class="right">%(input_str)s
   <input type="hidden" name="fid" value="%(fid)s">
   <input title="update" type="submit" value="u"/>
  </span>
  <input type="hidden" name="filter" value="%(clsname)s">
  <input type="hidden" name="path" value="%(path)s">%(input_query)s
 </form>
 <span class="right">
  <form action="%(remove_url)s">
   <input type="hidden" name="path" value="%(path)s">
   <input type="hidden" name="fid" value="%(fid)s">
   <input title="remove" type="submit" value="-"/>%(existing_query)s
  </form>
 </span>
</div>
"""

class H1DSFilterNode(template.Node):
    def __init__(self, filter_name, is_active=False, fid=None, filter_data=None):
        """
        Arguments:
        filter_name -- name of filter in template

        Keyword arguments:
        is_active -- set to True if this is an active filter (default: False)
        filter_data -- name of template variable containing filter parameters, used only if if_active=True to prefill form with currently used filter parameters.
        """
        self.filter_var = template.Variable(filter_name)
        self.is_active = is_active
        #self.filter_data_var = template.Variable(filter_data)
        self.filter_data_str = filter_data
        self.fid_str = fid
        
    def render(self, context):
        try:
            filter_instance = self.filter_var.resolve(context)
            request = context['request']
            existing_query_string = ''.join(['<input type="hidden" name="%s" value="%s" />' %(k,v) for k,v in request.GET.items()])
            if self.is_active:
                if self.filter_data_str != None:
                    filter_data_var = template.Variable(self.filter_data_str)
                    filter_data = filter_data_var.resolve(context)
                else:
                    filter_data = ""
                filter_id_var = template.Variable(self.fid_str)
                filter_id = filter_id_var.resolve(context)
                update_url = reverse("update-filter")
                remove_url = reverse("remove-filter")

                split_args = filter_data.split('_')
                input_str = ''.join(['<input title="%(name)s" type="text" size=5 name="%(name)s" value="%(value)s">' %{'name':j,'value':split_args[i]} for i,j in enumerate(filter_instance.template_info['args'])])

                return_string = active_filter_html %{
                    'update_url':update_url,
                    'text':filter_instance.template_info['text'],
                    'input_str':input_str,
                    'clsname':filter_instance.__name__,
                    'path':request.path,
                    'input_query':existing_query_string,
                    'fid':filter_id,
                    'remove_url':remove_url,
                    'existing_query':existing_query_string,
                    }
                return return_string

            else:
                submit_url = reverse("apply-filter")
                input_str = ''.join(['<input title="%(name)s" type="text" size=5 name="%(name)s">' %{'name':j} for i,j in enumerate(filter_instance.template_info['args'])])

                return_string =  filter_html %{'text':filter_instance.template_info['text'],
                                               'input_str':input_str,
                                               'clsname':filter_instance.__name__,
                                               'submit_url':submit_url,
                                               'path':request.path,
                                               'input_query':existing_query_string}
                return return_string
        except template.VariableDoesNotExist:
            #return ''
            raise

def show_filter(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, filter_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return H1DSFilterNode(filter_name)

def show_active_filter(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, filter_name, fid, filter_data = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a 3 arguments" % token.contents.split()[0]
    return H1DSFilterNode(filter_name, fid=fid, is_active=True, filter_data=filter_data)


register.tag('show_filter', show_filter)
register.tag('show_active_filter', show_active_filter)


class H1DSViewNode(template.Node):
    def __init__(self, view_name):
        self.view_name_var = template.Variable(view_name)

    def render(self, context):
        try:
            view_name = self.view_name_var.resolve(context)
            request = context['request']
            qd_copy = request.GET.copy()
            qd_copy.update({'view': view_name})
            link_url = '?'.join([request.path, qd_copy.urlencode()])
            return '<a href="%s">%s</a>' %(link_url, view_name)
        except template.VariableDoesNotExist:
            return ''

def show_view(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, view_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return H1DSViewNode(view_name)

register.tag('show_view', show_view)


class GetAbsoluteUriNode(template.Node):
    def __init__(self):
        pass

    def render(self, context):
        try:
            request = context['request']
            return request.build_absolute_uri()

        except template.VariableDoesNotExist:
            return ''

def get_absolute_uri(parser, token):
    return GetAbsoluteUriNode()

register.tag('get_absolute_uri', get_absolute_uri)


