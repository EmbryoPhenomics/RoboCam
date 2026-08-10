import dash
from dash import dcc
import dash_daq as daq
from dash import html
from dash import dash_table
import dash_bootstrap_components as dbc


# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "40rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow-y": "auto",   
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "42rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '3px',
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#6E6E6E',
    'color': 'white',
    'padding': '3px'
}

tab_selected_style_sub_main = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#424242',
    'color': 'white',
    'padding': '3px'
}

tab_selected_style_main = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#848484',
    'color': 'white',
    'padding': '3px'
}

def app_layout(sensor_modes):
    camera_options = []
    for i,mode in enumerate(sensor_modes):
        w,h = mode['size']
        camera_options.append(dict(label=f'{w}x{h}', value=i))


    # Experiment settings
    experimental_settings = html.Div(children=[
        dcc.Upload(
            id='upload-config',
            children=html.Div([
                'Drag and Drop or ',
                html.B('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            # Allow multiple files to be uploaded
            multiple=False
        ),
        html.Div(id='output-config-upload'),
    ], style={'width': '100%', 'display': 'table'})

    # XYZ controls
    xyz_controls = html.Div([
            html.Div(children=[
                html.Div(children=[
                    html.Br(),
                    dbc.Button('Set Origin', id='home-xy-button', size='lg'),
                    html.Div(id='xyz-homing-callback'),
                    html.Div(id='xyz-homing-set-origin'),
                ], style={'width': '40%', 'display': 'table-cell'}),
                html.Div(children=[
                    html.Br(),
                ], style={'width': '10%', 'display': 'table-cell'}),
                html.Div(children=[
                    html.Label('Step-size:'),
                    # dcc.Dropdown(
                    #     id='xyz-magnitude',
                    #     options=[
                    #         dict(label='0.001mm', value=0.001),
                    #         dict(label='0.01mm', value=0.01),
                    #         dict(label='0.1mm', value=0.1),
                    #         dict(label='1mm', value=1),
                    #         dict(label='10mm', value=10)],
                    #     value=10),

                    html.Div(children=[
                            dbc.RadioItems(
                                id="xyz-magnitude",
                                className="btn-group",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-primary",
                                labelCheckedClassName="active",
                                options=[
                                    {"label": "0.01mm", "value": 0.01},
                                    {"label": "0.1mm", "value": 0.1},
                                    {"label": "1mm", "value": 1},
                                    {"label": "10mm", "value": 10},
                                ],
                                value=1,
                    )], className="radio-group"),
                ], style={'width': '50%', 'display': 'table-cell'}),
            ], style={'width': '100%', 'display': 'table'}),

            html.Div(id='initial-xy'),

            html.Div(children=[
                html.Br(),

                html.Div(className='row', children=[
                    html.Div(className='eight columns', children=[
                        html.Div(children=[
                            html.Div(children=[
                                dbc.Button(html.I(className='fa-solid fa-square-arrow-up-right fa-flip-horizontal fa-2xl'), color='dark', size='lg', id='left-diag-xy-up'),
                            ], style={'width': '33%', 'display': 'table-cell'}),
                            html.Div(children=[
                                dbc.Button(html.I(className='fa-solid fa-arrow-up fa-2xl'), color='dark', size='lg', id='up-xy'),
                            ], style={'width': '33%', 'display': 'table-cell'}),
                            html.Div(children=[
                                dbc.Button(html.I(className='fa-solid fa-square-arrow-up-right fa-2xl'), color='dark', size='lg', id='right-diag-xy-up'),
                            ], style={'width': '33%', 'display': 'table-cell'}),
                        ], style={'width': '100%', 'display': 'table'}),

                        html.Br(),

                        html.Div(children=[
                            html.Div(children=[
                                dbc.Button(html.I(className='fa-solid fa-arrow-left fa-2xl'), color='dark', size='lg', id='left-xy')
                            ], style={'width': '33%', 'display': 'table-cell'}),
                            html.Div(children=[
                                dbc.Label(children='XY-Axis', align='right'),
                            ], style={'width': '33%', 'display': 'table-cell'}),
                            html.Div(children=[
                                dbc.Button(html.I(className='fa-solid fa-arrow-right fa-2xl'), color='dark', size='lg', id='right-xy')
                            ], style={'width': '33%', 'display': 'table-cell'}),
                        ], style={'width': '100%', 'display': 'table'}),
                        html.Br(),

                        html.Div(children=[
                            html.Div(children=[
                                dbc.Button(html.I(className='fa-solid fa-square-arrow-up-right fa-rotate-180 fa-2xl'), color='dark', size='lg', id='left-diag-xy-down')
                            ], style={'width': '33%', 'display': 'table-cell'}),
                            html.Div(children=[
                                dbc.Button(html.I(className='fa-solid fa-arrow-down fa-2xl'), color='dark', size='lg', id='down-xy')
                            ], style={'width': '33%', 'display': 'table-cell'}),
                            html.Div(children=[
                                dbc.Button(html.I(className='fa-solid fa-square-arrow-up-right fa-rotate-90 fa-2xl'), color='dark', size='lg', id='right-diag-xy-down')
                            ], style={'width': '33%', 'display': 'table-cell'}),
                        ], style={'width': '100%', 'display': 'table'}),
                    ]),
                    html.Div(className='four columns', children=[
                        dbc.Button(html.I(className='fa-solid fa-arrow-up fa-2xl'), color='dark', size='lg', id='up-z'),
                        html.Br(),
                        html.Br(),
                        dbc.Label(children='Z-Axis', align='right'),
                        html.Br(),
                        dbc.Button(html.I(className='fa-solid fa-arrow-down fa-2xl'), color='dark', size='lg', id='down-z'),
                    ]),

                    html.Div(children=[
                        html.Div(id='left-diag-xy-up-div'),
                        html.Div(id='up-xy-div'),
                        html.Div(id='right-diag-xy-up-div'),

                        html.Div(id='left-xy-div'),
                        html.Div(id='right-xy-div'),

                        html.Div(id='left-diag-xy-down-div'),
                        html.Div(id='down-xy-div'),
                        html.Div(id='right-diag-xy-down-div'),

                        html.Div(id='up-z-div'),
                        html.Div(id='down-z-div'),

                    ])
                ])
            ])
        ])

    # XYZ calibration
    xyz_calibration = html.Div([

            html.Div(children=[
                html.Div(children=[
                    dbc.Button('Record', id='grab-xy-calibration', size='lg'),
                    html.Div(id='grab-xy-calibration-callback')
                ], style={'width': '40%', 'display': 'table-cell'}),

                html.Div(children=[
                    dcc.Dropdown(
                        id='dot_diameters',
                        placeholder='Select dot diameter...',
                        options=[
                            dict(label="0.07mm", value=0.07),
                            dict(label="0.15mm", value=0.15),
                            dict(label="Crosshairs", value=None),
                            dict(label="0.6mm", value=0.6),
                            dict(label="1.5mm", value=1.5),
                        ]) 
                ], style={'width': '60%', 'display': 'table-cell'}),
            ], style={'width': '100%', 'display': 'table'}),

            html.Br(),
            
            dash_table.DataTable(
                id='xy_calibration_data',
                columns=[
                    dict(name='X', id='x'), 
                    dict(name='Y', id='y'), 
                    dict(name='Z', id='z'),
                    dict(name='Diameter', id='diameter_mm')],
                style_cell={'textAlign': 'left'},
                style_cell_conditional=[{'if': {'column_id': col},'width': '20%'} for col in ['x','y','z']],
                fixed_rows={'headers': True},
                style_table={'height': 200},
                editable=False,
                row_deletable=True,
                page_size=200
            ),

            dbc.Button('Set Calibration', id='calibrate-xy-button', size='lg', disabled=True),
            dcc.Interval(id='calibration_progress_interval', disabled=True),
            html.Div(id='calibration_progress_state'),
            html.Div(id='calibration_state'),
            html.Br(),

            html.Div(children=[
                html.Div(children=[
                    html.Label("Calibration scale (px/mm): ")
                ], style={'width': '70%', 'display': 'table-cell'}),
                html.Div(children=[
                    html.Br()
                ], style={'width': '5%', 'display': 'table-cell'}),
                html.Div(children=[
                    html.Div(id='calibration-output'),
                ], style={'width': '25%', 'display': 'table-cell'}),
            ], style={'width': '100%', 'display': 'table'}),

    ])

    # XYZ positions
    xyz_positions = html.Div([
                html.Div(children=[
                    html.Div(children=[
                        dbc.Button('Current', id='grab-xy', size='lg'),
                        html.Div(id='grab-xy-callback')
                    ], style={'width': '30%', 'display': 'table-cell'}),

                    html.Div(children=[
                        html.Br()
                    ], style={'width': '5%', 'display': 'table-cell'}),

                    html.Div(children=[
                        dbc.Button('Replace', id='replace-xy-button', size='lg'),
                        html.Div(id='replace-xy-callback')
                    ], style={'width': '30%', 'display': 'table-cell'}),

                    html.Div(children=[
                        html.Br()
                    ], style={'width': '5%', 'display': 'table-cell'}),

                    html.Div(children=[
                        dbc.Button('Remove', id='remove-xy-button', size='lg'),
                        html.Div(id='remove-xy-callback')
                    ], style={'width': '30%', 'display': 'table-cell'}),

                    html.Div(children=[], style={'width': '80%', 'display': 'table-cell'}),

                ], style={'width': '100%', 'display': 'table'}),

                html.Br(),

                dash_table.DataTable(
                    id='xy_coords',
                    columns=[
                        dict(name='X', id='x'), 
                        dict(name='Y', id='y'), 
                        dict(name='Z', id='z'),
                        dict(name='Label', id='label')],
                    style_cell={'textAlign': 'left'},
                    style_cell_conditional=[{'if': {'column_id': col},'width': '20%'} for col in ['x','y','z']],
                    fixed_rows={'headers': True},
                    style_table={'height': 300},
                    row_selectable='single',
                    editable=True,
                    page_size=300
                )
        ])

    # Experimental setup
    experimental_setup = html.Div([
                html.Label(children='Number of positions'),
                dcc.RadioItems(
                    id='acquisition-number',
                    options=[
                        {'label': 'Single', 'value': 'Single'},
                        {'label': 'Multiple', 'value': 'Multiple'}],
                    value='Single',
                    labelStyle={'display': 'inline-block'}),

                html.Div(id='acquisition-number-change'),

                html.Br(),

                html.Div(children=[
                    html.Div(children=[
                        html.Label(children='Number of time-points')
                    ], style={'width': '70%', 'display': 'table-cell'}),
                    html.Div(children=[
                        daq.NumericInput(id='total-time-points', min=1, max=100000, value=1, size=100)
                    ], style={'width': '30%', 'display': 'table-cell'}),
                ], style={'width': '100%', 'display': 'table'}),

                html.Div(id='total-time-points-change'),

                html.Div(children=[
                    html.Div(children=[
                        html.Label(children='Acquisition interval (mins)')
                    ], style={'width': '70%', 'display': 'table-cell'}),
                    html.Div(children=[
                        daq.NumericInput(id='acq-length', min=0, max=100000, value=1, size=100)
                    ], style={'width': '30%', 'display': 'table-cell'}),
                ], style={'width': '100%', 'display': 'table'}),

                html.Div(id='acq-length-change'),

                html.Div(children=[
                    html.Div(children=[
                        html.Label(children='Acquisition length (secs)')
                    ], style={'width': '70%', 'display': 'table-cell'}),
                    html.Div(children=[
                        daq.NumericInput(id='each-time-limit', min=1, max=100000, value=1, size=100)
                    ], style={'width': '30%', 'display': 'table-cell'}),
                ], style={'width': '100%', 'display': 'table'}),

                html.Div(id='each-time-limit-change'),

                html.Br(),

                html.Label('Drive and Folder selection:'),

                html.Div(children=[
                    html.Div(children=[
                        dcc.Input(
                            id='acquire-path-input', 
                            type='text',
                            placeholder='Specify a folder to save video for the drive selected...',),
                    ], style={'width': '70%', 'display': 'table-cell'}),
                    html.Div(children=[
                        dbc.Button('Select', id='path-select', size='lg'),
                    ], style={'width': '30%', 'display': 'table-cell'}),
                ], style={'width': '100%', 'display': 'table'}),

                html.Div(id='acquire-outpath-check'),
                html.Div(id='acquire-path-input-change'),

                html.Br(),

                html.Div(children=[
                    html.Div(children=[
                        html.Label(children='Turn off light between timepoints:')
                    ], style={'width': '50%', 'display': 'table-cell'}),
                    html.Div(children=[
                        daq.ToggleSwitch(
                            id='light-auto-dimming',
                            value=False,
                            label=['Yes', 'No']),
                    ], style={'width': '50%', 'display': 'table-cell'}),
                ], style={'width': '100%', 'display': 'table'}),

                # html.Div(children=[
                #     html.Div(children=[
                #         html.Label(children='Disk space (available/total)')
                #     ], style={'width': '50%', 'display': 'table-cell'}),
                #     html.Div(children=[
                #         html.Label(id='disk_space_text')
                #     ], style={'width': '50%', 'display': 'table-cell'}),
                # ], style={'width': '100%', 'display': 'table'}),

                # html.Br(),

                # html.Div(children=[
                #     html.Div(children=[
                #         html.Label(children='Projected usage')
                #     ], style={'width': '50%', 'display': 'table-cell'}),
                #     html.Div(children=[
                #         html.Label(id='projected_usage_text')
                #     ], style={'width': '50%', 'display': 'table-cell'}),
                # ], style={'width': '100%', 'display': 'table'}),

                html.Br(),

                dbc.Button('Start acquisition', id='acquire-button', size='lg'),
                dbc.Button('Cancel acquisition', id='cancel-acquire-button', size='lg'),
                html.Div(id='acquisition_state'),
                html.Div(id='cancel_state'),
                html.Div(id='acquisition_progress_state'),

                dcc.Interval(id='acquisition_progress_interval', disabled=True),

                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Acquisition Error")),
                        dbc.ModalBody("Cannot save files due to a space in your folder path. Please make sure there are no spaces in your folder name."),
                    ],
                    id="acquisition-folder-name-popup",
                    is_open=False,
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Acquisition Error")),
                        dbc.ModalBody("Please cancel the live stream before starting an acquisition."),
                    ],
                    id="acquisition-live-stream-popup",
                    is_open=False,
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Acquisition Error")),
                        dbc.ModalBody("Files already in folder, please change folder to not overwrite existing data."),
                    ],
                    id="acquisition-folder-popup",
                    is_open=False,
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Acquisition Error")),
                        dbc.ModalBody("Time to scan per timepoint is greater than the interval requested. Please set a greater timepoint interval."),
                    ],
                    id="acquisition-interval-popup",
                    is_open=False,
                ),
            ])

    # XYZ view
    xyz_view = html.Div([

            html.Div(children=[
                html.Div(children=[
                    html.Label('Activate graph')
                ], style={'width': '50%', 'display': 'table-cell'}),

                html.Div(children=[
                    daq.ToggleSwitch(
                        id='activate-graph-switch',
                        value=False,
                        label=['Off', 'On'])
                ], style={'width': '50%', 'display': 'table-cell'})
            ], style={'width': '100%', 'display': 'table'}),

            html.Div(children=[
                html.Div(children=[
                    html.Label('Dimensions')
                ], style={'width': '50%', 'display': 'table-cell'}),

                html.Div(children=[
                    daq.ToggleSwitch(
                        id='dimensions-switch',
                        value=False,
                        label=['2D', '3D'])
                ], style={'width': '50%', 'display': 'table-cell'})
            ], style={'width': '100%', 'display': 'table'}),

            html.Br(),

            html.Label('Select required positions'),
            html.Div(children=[
                html.Div(children=[
                    html.Label('Top left'),
                    dcc.Dropdown(
                        id='top_left_position_generate_xy',
                        placeholder='Please select a position...',
                        options=[],
                        disabled=False)               
                ], style={'width': '30%', 'display': 'table-cell'}),
                html.Div(children=[
                    html.Label('Top right'),
                    dcc.Dropdown(
                        id='top_right_position_generate_xy',
                        placeholder='Please select a position...',
                        options=[],
                        disabled=True)  
                ], style={'width': '30%', 'display': 'table-cell'}),
                html.Div(children=[
                    html.Label('Bottom right'),
                    dcc.Dropdown(
                        id='bottom_right_position_generate_xy',
                        placeholder='Please select a position...',
                        options=[],
                        disabled=True)  
                ], style={'width': '30%', 'display': 'table-cell'})
            ], style={'width': '100%', 'display': 'table'}),

            html.Br(),

            html.Label('Select position requirements'),
            html.Div(children=[
                html.Div(children=[
                    html.Label('Number of Columns'),
                    daq.NumericInput(id='pos_gen_ncols', min  =1, max=100, value=1, size=100),        
                ], style={'width': '40%', 'display': 'table-cell'}),
                html.Div(children=[
                    html.Label('Number of Rows'),
                    daq.NumericInput(id='pos_gen_nrows', min=1, max=100, value=1, size=100),        
                ], style={'width': '40%', 'display': 'table-cell'}),
            ], style={'width': '100%', 'display': 'table'}),

            html.Br(),

            dbc.Button('Generate xy', id='generate-xy-button', disabled=False, size='lg'),



            # html.Div(children=[
            #     html.Div(children=[
            #         dbc.Button('Generate xy', id='generate-xy-button', disabled=True, size='lg')
            #     ], style={'width': '40%', 'display': 'table-cell'}),
            #     html.Div(children=[
            #         dcc.Dropdown(
            #             id='plate-size',
            #             placeholder='Please select a plate size...',
            #             options=[
            #                 dict(label='24 wells', value=24),
            #                 dict(label='48 wells', value=48),
            #                 dict(label='96 wells', value=96),
            #                 dict(label='384 wells', value=384)],
            #             disabled=True)
            #     ], style={'width': '60%', 'display': 'table-cell'})
            # ], style={'width': '100%', 'display': 'table'}),
            # html.P('Note that you need position A1 to generate positions.'),

            html.Div(id='generate-xy-callback'),
            html.Div(id='load-xy-callback'),

            html.Div(id='coord-graph-div', children=[]),      
            html.Div(id='graph-xy-move')
    ])

    experimental_progress = html.Div([
        html.Label('Current timepoint:'),
        dbc.Progress(id="timepoint-pg", style={'height': '20px'}),
        html.Br(),
        html.Label('Current embryo:'),
        dbc.Progress(id="embryo-pg", style={'height': '20px'})
    ])

    # Camera settings
    camera_settings = html.Div(children=[
        dcc.Tabs(
            id='camera-settings-tabs',
            value='led-tab',
            children=[
                dcc.Tab(label='LED', value='led-tab', style=tab_style, selected_style=tab_selected_style_main, children=[
                    html.Br(),
                    html.Label('Brightness of the LED ring.'),
                    dcc.Slider(
                        id='hardware-brightness',
                        min=0,
                        max=100,
                        value=0,
                        tooltip={'always_visible': True, 'placement': 'bottom'},
                        persistence=True),
                    html.Div(id='hardware-brightness-callback'),
                ]),
                dcc.Tab(label='Exposure', value='exposure-tab', style=tab_style, selected_style=tab_selected_style_main, children=[
                    html.Br(),
                    html.Label('Shutter speed for the camera sensor to use, in milliseconds.'),
                    dcc.Slider(
                        id='exposure',
                        min=0,
                        max=100,
                        value=20,
                        tooltip={'always_visible': True, 'placement': 'bottom'},
                        persistence=True),
                    html.Div(id='exposure-change'),
                ]),
                dcc.Tab(label='Gain', value='gain-tab', style=tab_style, selected_style=tab_selected_style_main, children=[
                    html.Br(),
                    html.Label('Analogue gain applied by the camera sensor.'),
                    dcc.Slider(
                        id='analogue_gain',
                        min=0,
                        max=20,
                        value=1,
                        tooltip={'always_visible': True, 'placement': 'bottom'},
                        persistence=True),
                    html.Div(id='analogue_gain-change'),
                ]),                    
                dcc.Tab(label='FPS', value='fps-tab', style=tab_style, selected_style=tab_selected_style_main, children=[
                    html.Br(),
                    html.Label('Frames per second the camera sensor delivers.'),
                    dcc.Slider(
                        id='fps',
                        min=0,
                        max=100,
                        value=30,
                        tooltip={'always_visible': True, 'placement': 'bottom'},
                        persistence=True),
                    html.Div(id='fps-change'),
                ])
            ]),
            
            html.Br(),

            html.Div(children=[
                html.Div(children=[
                    html.Label(children='Resolution'),
                    dcc.Dropdown(
                        id='resolution-preset',
                        placeholder='Please select a resolution...',
                        value=0,
                        options=camera_options,
                        disabled=False,
                        persistence=True,
                        persistence_type='session'),
                ], style={'width': '50%', 'display': 'table-cell'}),

                html.Div(children=[
                    html.Br(),
                ], style={'width': '15%', 'display': 'table-cell'}),

                html.Div(children=[
                    html.Br(),
                    dbc.Button('Update', id='update-camera-settings', size='lg'),
                    html.Div(id='hidden-update-callback'),
                ], style={'width': '35%', 'display': 'table-cell'}),                                            
            ], style={'width': '100%', 'display': 'table'}),

            html.Div(id='resolution-preset-change'),

            html.Br(),

            html.Label('Camera streaming mode'),
            daq.ToggleSwitch(
                id='camera-streaming-mode',
                value=False,
                label=['Browser', 'Desktop']),

            html.Br(),

            html.Div(children=[
                html.Div(children=[
                    dbc.Button('Snap', id='test-frame-button', size='lg')
                ], style={'width': '20%', 'display': 'table-cell'}),
                html.Div(children=[
                    dbc.Button('Start/Stop Stream', id='camera-live-stream', size='lg'),
                ], style={'width': '60%', 'display': 'table-cell'}),
                html.Div(children=[
                    html.Div(id='streaming-spinner')
                ], style={'width': '`20%', 'display': 'table-cell'}),
            ], style={'width': '100%', 'display': 'table'}),

        ])



    sidebar = html.Div(
        [
            html.Div(id='loaded-data-callback'),
            html.Div(id='hiddenFPSdata'),
            html.Div(id='fullROIData'),
            html.Div(id='config-save-callback'),
            html.Div(id='connect-cam-callback'),

            html.H2("RoboCam App", className="display-4"),
            html.Br(),
            dbc.Card([
                dbc.CardBody([
                    dbc.Accordion([
                        dbc.AccordionItem(title=html.Label("Experiment settings", className="fs-3"), children=[
                            experimental_settings
                        ]),
                        dbc.AccordionItem(title=html.Label("Camera settings", className="fs-3"), children=[
                            camera_settings
                        ]),
                        dbc.AccordionItem(title=html.Label("XYZ controls", className="fs-3"), children=[
                            xyz_controls
                        ]),
                        dbc.AccordionItem(title=html.Label("XYZ calibration", className="fs-3"), children=[
                            xyz_calibration
                        ]),
                        dbc.AccordionItem(title=html.Label("XYZ positions", className="fs-3"), children=[
                            xyz_positions
                        ]),
                        dbc.AccordionItem(title=html.Label("XYZ graph", className="fs-3"), children=[
                            xyz_view
                        ]),
                        dbc.AccordionItem(title=html.Label("Experiment setup", className="fs-3"), children=[
                            experimental_setup
                        ]),
                        dbc.AccordionItem(title=html.Label("Experiment progress", className="fs-3"), children=[
                            experimental_progress
                        ]),
                    ], start_collapsed=True, always_open=True)
                ])
            ]),
        ],
        style=SIDEBAR_STYLE,
    )

    content = html.Div(id="page-content", style=CONTENT_STYLE, children=[
        dcc.Tabs(
            id='image-capture-tabs',
            value='still-tab',
            children=[
                dcc.Tab(label='Still Image', value='still-tab', style=tab_style, selected_style=tab_selected_style_main, children=[
                    html.Div(id='still-image', children=[])
                ]),
                dcc.Tab(label='Live Stream', value='stream-tab', style=tab_style, selected_style=tab_selected_style_main, children=[
                    html.Div([
                    html.Br(),
                    html.Img(src="/video_feed")
            ], className="mx-auto", style={"width": "90rem", "height": "60rem"}),
                ])
            ]
        ),
        html.Div(id='image-capture-tab-state-still', children=[]),
        html.Div(id='image-capture-tab-state-stream', children=[]),
        html.Div(children=[], id='camera-state-live-view'),
        html.Div(children=[], id='camera-state-snapshot'),

    ])

    return html.Div([sidebar, content])


if __name__ == '__main__':
    import dash
    import os
    import shutil
    from dash.long_callback import DiskcacheLongCallbackManager

    from flask import request, Flask, Response

    ## Diskcache
    import diskcache

    cache = diskcache.Cache('./cache')
    long_callback_manager = DiskcacheLongCallbackManager(cache)

    # Initialise app
    sensor_modes = [{'bit_depth': 10,
                    'fps': 120.05,
                    'size': (1332, 990),
                    'unpacked': 'SRGGB10'}]

    server = Flask(__name__)
    app = dash.Dash(__name__, server=server, long_callback_manager=long_callback_manager, external_stylesheets=[dbc.themes.BOOTSTRAP, './assets/app.css', dbc.icons.FONT_AWESOME])
    app.config['suppress_callback_exceptions'] = True 
    app.layout = app_layout(sensor_modes)

    app.run_server(debug=True)
