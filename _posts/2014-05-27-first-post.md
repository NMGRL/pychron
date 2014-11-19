---
layout: post
title: My first blog entry
author: Jake Ross
comments: True
---
this is my first blog entry

here is a python code snippet
{% raw %}
    {% highlight python %}
    def main():
        print "hello world"
    {% endhighlight %}
{% endraw %}

Rendered as

{% highlight python %}
def main():
    print "hello world"
{% endhighlight %}

{% highlight ruby linenos%}
    def show
      @widget = Widget(params[:id])
      respond_to do |format|
        format.html # show.html.erb
        format.json { render json: @widget }
      end
    end
{% endhighlight %}
