from django import template
from django.core.urlresolvers import reverse

register = template.Library()

class MDSDataTemplateNode(template.Node):
    def __init__(self, data_name):
        self.data_var = template.Variable(data_name)
    def render(self, context):
        try:
            data = self.data_var.resolve(context)
            #return '<div class="centrecontent"><div class="label">%s</div><div class="data">%s</div></div>' %(data.filtered_dtype, data.get_view('html'))
            return '<div class="centrecontent"><div class="label">%s</div><div class="data">%s</div></div>' %("DATATYPE LABEL?", data.get_view('html'))
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

def get_filter(context, filter_instance, is_active=False, fid=None, filter_data=None):
    try:
        request = context['request']
        existing_query_string = ''.join(['<input type="hidden" name="%s" value="%s" />' %(k,v) for k,v in request.GET.items()])
        if is_active:
            if filter_data == None:
                filter_data = ""
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
                'fid':fid,
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

@register.simple_tag(takes_context=True)
def show_filters(context, mdsnode):
    return "".join([get_filter(context, f) for f in mdsnode.available_filters])


@register.simple_tag(takes_context=True)
def show_active_filters(context, mdsnode):
    return "".join([get_filter(context, f, is_active=True, fid=fid, filter_data=fdata) for fid, f, fdata in mdsnode.filter_history])



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


