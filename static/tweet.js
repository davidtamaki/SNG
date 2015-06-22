
////////////
/* MODELS */
////////////


// var Tweet = Backbone.Model.extend({
//     defaults: {
//         screen_name: "xyz",
//         message: "lalala"
//     }
// });

var Tweet = Backbone.Model.extend();

var Tweets = Backbone.Collection.extend({
    url: '/api/events....',
    model: Tweet,

    parse: function(response) {
        return response.results;
    },

    sync: function(method, model, options) {
        var that = this;
        var params = _.extend({
            type: 'GET',
            dataType: 'jsonp',
            url: that.url,
            processData: false
        }, options);

        return $.ajax(params);
    }
});





///////////
/* VIEWS */
///////////

TweetsView = Backbone.View.extend({
    initialize: function() {
      _.bindAll(this, 'render');
      // create a collection
      this.collection = new Tweets;
      // Fetch the collection and call render() method
      var that = this;
      this.collection.fetch({
        success: function () {
            that.render();
        }
      });
    },

    // Use an extern template
    //template: _.template($('#tweetsTemplate').html()),
    tweet_template: _.template('<%= screen_name %>  says <%= message %>'), // inline template

    render: function() {
        // Fill the html with the template and the collection
        $(this.el).html(this.template({ tweets: this.collection.toJSON() }));
    }
});

var app = new TweetsView({
    // define the el where the view will render
    el: $('body')
});

